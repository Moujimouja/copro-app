"""
API endpoints pour les administrateurs
- Gestion des équipements (ServiceInstance)
- Changement de statut des équipements
- Création et gestion des incidents
- Gestion des tickets
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from sqlalchemy import func as sql_func, and_
from app.db import get_db
from app.models.copro import Copro, Building, ServiceInstance
from app.models.status import Incident, IncidentUpdate as IncidentUpdateModel, IncidentComment, IncidentStatus
from app.models.ticket import Ticket, TicketStatus, TicketType
from app.models.ticket_comment import TicketComment
from app.models.user import User
from app.models.maintenance import Maintenance
from app.auth import get_current_user, get_password_hash

router = APIRouter()


# ============ Schemas ============

class ServiceInstanceStatusUpdate(BaseModel):
    status: str  # operational, degraded, partial_outage, major_outage, maintenance


class ServiceInstanceCreate(BaseModel):
    building_id: int
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: str = "operational"
    order: int = 0


class ServiceInstanceUpdate(BaseModel):
    building_id: Optional[int] = None
    name: Optional[str] = None
    identifier: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceInstanceResponse(BaseModel):
    id: int
    copro_id: int
    building_id: int
    name: str
    identifier: Optional[str]
    description: Optional[str]
    location: Optional[str]
    status: str
    is_active: bool
    order: int
    building_name: str

    class Config:
        from_attributes = True


class IncidentCreate(BaseModel):
    service_instance_id: Optional[int] = None  # DEPRECATED: utiliser service_instance_ids
    service_instance_ids: Optional[List[int]] = None  # Liste des équipements concernés
    title: str
    message: str
    status: str = "investigating"
    is_scheduled: bool = False
    scheduled_for: Optional[datetime] = None
    created_at: Optional[datetime] = None  # Date de début réel de l'incident
    equipment_status: Optional[str] = None  # Statut à appliquer à l'équipement (degraded, partial_outage, major_outage, maintenance)


class IncidentUpdateCreate(BaseModel):
    message: str
    status: str


class TicketReview(BaseModel):
    status: str  # approved, rejected (deprecated, utiliser update_status)
    admin_notes: Optional[str] = None  # Deprecated, utiliser les commentaires
    create_incident: bool = False  # Si True, créer un incident automatiquement


class TicketAssign(BaseModel):
    assigned_to: int  # ID de l'administrateur


class TicketStatusUpdate(BaseModel):
    status: str  # analyzing, in_progress, resolved, closed


class TicketCommentCreate(BaseModel):
    comment: str


class IncidentStatusUpdate(BaseModel):
    status: str


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    service_instance_id: Optional[int] = None
    created_at: Optional[datetime] = None  # Date de début réel de l'incident
    resolved_at: Optional[datetime] = None  # Date de résolution


class IncidentCommentCreate(BaseModel):
    comment: str


# ============ Vérification Admin ============

async def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Vérifier que l'utilisateur est admin"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user


# ============ Gestion de la Copropriété ============

class CoproCreate(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "France"


class CoproUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class CoproResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    city: Optional[str]
    postal_code: Optional[str]
    country: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/copro", response_model=CoproResponse)
async def get_copro(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir la copropriété (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    return copro




@router.post("/copro", response_model=CoproResponse, status_code=status.HTTP_201_CREATED)
async def create_copro(
    copro_data: CoproCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer une copropriété (admin uniquement)"""
    # Vérifier s'il existe déjà une copropriété active
    existing = db.query(Copro).filter(Copro.is_active == True).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Une copropriété active existe déjà. Modifiez-la ou désactivez-la d'abord."
        )
    
    db_copro = Copro(
        name=copro_data.name,
        address=copro_data.address,
        city=copro_data.city,
        postal_code=copro_data.postal_code,
        country=copro_data.country,
        is_active=True
    )
    
    db.add(db_copro)
    db.commit()
    db.refresh(db_copro)
    
    return db_copro


@router.put("/copro/{copro_id}", response_model=CoproResponse)
async def update_copro(
    copro_id: int,
    copro_update: CoproUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour la copropriété (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.id == copro_id).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Copropriété non trouvée")
    
    update_data = copro_update.dict(exclude_unset=True)
    
    # Appliquer les mises à jour
    for field, value in update_data.items():
        setattr(copro, field, value)
    
    copro.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(copro)
    
    return copro


# ============ Gestion des Bâtiments et Types de Services ============

class BuildingCreate(BaseModel):
    name: str  # Nom unique du bâtiment
    description: Optional[str] = None
    order: int = 0


class BuildingUpdate(BaseModel):
    name: Optional[str] = None  # Nom unique du bâtiment
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class BuildingResponse(BaseModel):
    id: int
    copro_id: int
    name: str  # Nom unique du bâtiment
    description: Optional[str]
    order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/buildings", response_model=List[BuildingResponse])
async def list_buildings(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les bâtiments (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    buildings = db.query(Building).filter(
        Building.copro_id == copro.id
    ).order_by(Building.order, Building.name).all()
    
    return buildings


@router.get("/buildings/{building_id}", response_model=BuildingResponse)
async def get_building(
    building_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir un bâtiment par ID (admin uniquement)"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    return building


@router.post("/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    building: BuildingCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer un nouveau bâtiment (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Vérifier l'unicité du nom dans la copropriété
    existing = db.query(Building).filter(
        Building.copro_id == copro.id,
        Building.name == building.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un bâtiment avec le nom '{building.name}' existe déjà")
    
    db_building = Building(
        copro_id=copro.id,
        name=building.name,
        description=building.description,
        order=building.order
    )
    
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    
    return db_building


@router.put("/buildings/{building_id}", response_model=BuildingResponse)
async def update_building(
    building_id: int,
    building_update: BuildingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour un bâtiment (admin uniquement)"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    update_data = building_update.dict(exclude_unset=True)
    
    # Vérifier l'unicité du nom si modifié
    if 'name' in update_data and update_data['name'] != building.name:
        existing = db.query(Building).filter(
            Building.copro_id == building.copro_id,
            Building.name == update_data['name'],
            Building.id != building_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Un bâtiment avec le nom '{update_data['name']}' existe déjà")
    
    # Appliquer les mises à jour
    for field, value in update_data.items():
        setattr(building, field, value)
    
    building.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(building)
    
    return building


@router.delete("/buildings/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_building(
    building_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Supprimer un bâtiment (admin uniquement)"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Vérifier s'il y a des équipements associés
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.building_id == building_id
    ).count()
    
    if service_instances > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer ce bâtiment car {service_instances} équipement(s) y sont associés"
        )
    
    db.delete(building)
    db.commit()
    return None




# ============ Gestion des Équipements ============

@router.get("/service-instances", response_model=List[ServiceInstanceResponse])
async def list_service_instances(
    building_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les équipements (admin uniquement) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    query = db.query(ServiceInstance).filter(ServiceInstance.copro_id == copro.id)
    
    if building_id:
        query = query.filter(ServiceInstance.building_id == building_id)
    
    instances = query.order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    result = []
    for instance in instances:
        db.refresh(instance, ['building'])
        result.append(ServiceInstanceResponse(
            id=instance.id,
            copro_id=instance.copro_id,
            building_id=instance.building_id,
            name=instance.name,
            identifier=instance.identifier,
            description=instance.description,
            location=instance.location,
            status=instance.status,
            is_active=instance.is_active,
            order=instance.order,
            building_name=instance.building.name if instance.building else ""
        ))
    
    return result


@router.get("/service-instances/{instance_id}", response_model=ServiceInstanceResponse)
async def get_service_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir un équipement par ID (admin uniquement)"""
    instance = db.query(ServiceInstance).filter(ServiceInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    
    db.refresh(instance, ['building'])
    return ServiceInstanceResponse(
        id=instance.id,
        copro_id=instance.copro_id,
        building_id=instance.building_id,
        name=instance.name,
        identifier=instance.identifier,
        description=instance.description,
        location=instance.location,
        status=instance.status,
        is_active=instance.is_active,
        order=instance.order,
        building_name=instance.building.name if instance.building else ""
    )


@router.post("/service-instances", response_model=ServiceInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_service_instance(
    service_instance: ServiceInstanceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer un nouvel équipement (admin uniquement)"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Vérifier que le bâtiment existe et appartient à la copropriété
    building = db.query(Building).filter(
        Building.id == service_instance.building_id,
        Building.copro_id == copro.id
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Vérifier l'unicité du nom dans la copropriété
    existing = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.name == service_instance.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un équipement avec le nom '{service_instance.name}' existe déjà")
    
    # Valider le statut
    valid_statuses = ["operational", "degraded", "partial_outage", "major_outage", "maintenance"]
    if service_instance.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptées: {valid_statuses}")
    
    db_service_instance = ServiceInstance(
        copro_id=copro.id,
        building_id=service_instance.building_id,
        name=service_instance.name,
        identifier=service_instance.identifier,
        description=service_instance.description,
        location=service_instance.location,
        status=service_instance.status,
        order=service_instance.order
    )
    
    db.add(db_service_instance)
    db.commit()
    db.refresh(db_service_instance, ['building'])
    
    return ServiceInstanceResponse(
        id=db_service_instance.id,
        copro_id=db_service_instance.copro_id,
        building_id=db_service_instance.building_id,
        name=db_service_instance.name,
        identifier=db_service_instance.identifier,
        description=db_service_instance.description,
        location=db_service_instance.location,
        status=db_service_instance.status,
        is_active=db_service_instance.is_active,
        order=db_service_instance.order,
        building_name=db_service_instance.building.name if db_service_instance.building else ""
    )


@router.put("/service-instances/{instance_id}", response_model=ServiceInstanceResponse)
async def update_service_instance(
    instance_id: int,
    service_instance_update: ServiceInstanceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour un équipement (admin uniquement)"""
    instance = db.query(ServiceInstance).filter(ServiceInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    
    # Récupérer la copropriété
    copro = db.query(Copro).filter(Copro.id == instance.copro_id).first()
    
    # Mettre à jour les champs fournis
    update_data = service_instance_update.dict(exclude_unset=True)
    
    # Vérifier le bâtiment si fourni
    if 'building_id' in update_data:
        building = db.query(Building).filter(
            Building.id == update_data['building_id'],
            Building.copro_id == instance.copro_id
        ).first()
        if not building:
            raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Vérifier l'unicité du nom si fourni
    if 'name' in update_data and update_data['name'] != instance.name:
        existing = db.query(ServiceInstance).filter(
            ServiceInstance.copro_id == instance.copro_id,
            ServiceInstance.name == update_data['name'],
            ServiceInstance.id != instance_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Un équipement avec le nom '{update_data['name']}' existe déjà")
    
    # Valider le statut si fourni
    if 'status' in update_data:
        valid_statuses = ["operational", "degraded", "partial_outage", "major_outage", "maintenance"]
        if update_data['status'] not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptées: {valid_statuses}")
    
    # Appliquer les mises à jour
    for field, value in update_data.items():
        setattr(instance, field, value)
    
    instance.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(instance, ['building'])
    
    return ServiceInstanceResponse(
        id=instance.id,
        copro_id=instance.copro_id,
        building_id=instance.building_id,
        name=instance.name,
        identifier=instance.identifier,
        description=instance.description,
        location=instance.location,
        status=instance.status,
        is_active=instance.is_active,
        order=instance.order,
        building_name=instance.building.name if instance.building else ""
    )


@router.delete("/service-instances/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_instance(
    instance_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Supprimer un équipement (admin uniquement)"""
    instance = db.query(ServiceInstance).filter(ServiceInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    
    db.delete(instance)
    db.commit()
    return None


@router.patch("/service-instances/{instance_id}/status")
async def update_service_status(
    instance_id: int,
    status_update: ServiceInstanceStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Changer le statut d'un équipement (admin uniquement)"""
    instance = db.query(ServiceInstance).filter(ServiceInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Équipement non trouvé")
    
    # Valider le statut
    valid_statuses = ["operational", "degraded", "partial_outage", "major_outage", "maintenance"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptées: {valid_statuses}")
    
    instance.status = status_update.status
    instance.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(instance)
    
    return {"message": "Statut mis à jour", "instance": instance}


# ============ Gestion des Incidents ============

@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer un incident (admin uniquement) - crée un seul incident avec plusieurs équipements via table de liaison"""
    # Déterminer la liste des équipements
    equipment_ids = []
    if incident_data.service_instance_ids:
        equipment_ids = incident_data.service_instance_ids
    elif incident_data.service_instance_id:
        # Support de l'ancien format pour rétrocompatibilité
        equipment_ids = [incident_data.service_instance_id]
    
    # Si des équipements sont spécifiés, le statut de l'équipement est obligatoire
    if equipment_ids and not incident_data.equipment_status:
        raise HTTPException(
            status_code=400,
            detail="Le statut de l'équipement est obligatoire lorsqu'un ou plusieurs équipements sont sélectionnés"
        )
    
    # Valider le statut si fourni
    if incident_data.equipment_status:
        valid_statuses = ["degraded", "partial_outage", "major_outage", "maintenance"]
        if incident_data.equipment_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Statut d'équipement invalide. Valeurs acceptées: {valid_statuses}"
            )
    
    # Récupérer la copropriété (depuis le premier équipement ou la copropriété active)
    copro_id = None
    service_instances = []
    if equipment_ids:
        service_instances = db.query(ServiceInstance).filter(
            ServiceInstance.id.in_(equipment_ids)
        ).all()
        if len(service_instances) != len(equipment_ids):
            raise HTTPException(status_code=404, detail="Un ou plusieurs équipements non trouvés")
        copro_id = service_instances[0].copro_id
        
        # Vérifier que tous les équipements appartiennent à la même copropriété
        if not all(si.copro_id == copro_id for si in service_instances):
            raise HTTPException(
                status_code=400,
                detail="Tous les équipements doivent appartenir à la même copropriété"
            )
    else:
        # Si aucun équipement, utiliser la copropriété active
        copro = db.query(Copro).filter(Copro.is_active == True).first()
        if copro:
            copro_id = copro.id
    
    created_at = incident_data.created_at if incident_data.created_at else datetime.utcnow()
    
    # Créer un seul incident
    # Utiliser le premier équipement pour service_instance_id (rétrocompatibilité)
    first_service_instance_id = service_instances[0].id if service_instances else None
    
    incident = Incident(
        copro_id=copro_id,
        service_instance_id=first_service_instance_id,  # Pour rétrocompatibilité
        title=incident_data.title,
        message=incident_data.message,
        status=IncidentStatus(incident_data.status),
        is_scheduled=incident_data.is_scheduled,
        scheduled_for=incident_data.scheduled_for,
        created_at=created_at
    )
    db.add(incident)
    db.flush()
    
    # Associer tous les équipements via la table de liaison
    if service_instances:
        incident.service_instances = service_instances
        
        # Mettre à jour le statut de tous les équipements
        if incident_data.equipment_status:
            for service_instance in service_instances:
                service_instance.status = incident_data.equipment_status
                service_instance.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incident, ['service_instances'])
    
    return {"message": "Incident créé", "incident_id": incident.id}


@router.get("/incidents", response_model=List[dict])
async def list_incidents(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les incidents (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    query = db.query(Incident).filter(Incident.copro_id == copro.id)
    
    if status_filter:
        query = query.filter(Incident.status == IncidentStatus(status_filter))
    
    incidents = query.order_by(Incident.created_at.desc()).all()
    
    result = []
    for incident in incidents:
        db.refresh(incident, ['service_instance', 'service_instances'])
        # Récupérer le statut de l'équipement si un équipement est associé (pour rétrocompatibilité)
        equipment_status = None
        if incident.service_instance:
            equipment_status = incident.service_instance.status
        
        # Récupérer les noms des équipements (via la table de liaison ou service_instance pour rétrocompatibilité)
        service_instance_names = []
        if incident.service_instances and len(incident.service_instances) > 0:
            service_instance_names = [si.name for si in incident.service_instances]
        elif incident.service_instance:
            service_instance_names = [incident.service_instance.name]
        
        result.append({
            "id": incident.id,
            "title": incident.title,
            "message": incident.message,
            "status": incident.status.value,
            "service_instance": ", ".join(service_instance_names) if service_instance_names else None,  # Afficher tous les équipements
            "service_instance_id": incident.service_instance_id,  # Pour rétrocompatibilité
            "service_instance_ids": [si.id for si in incident.service_instances] if incident.service_instances else ([incident.service_instance_id] if incident.service_instance_id else []),
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "equipment_status": equipment_status,
        })
    
    return result


@router.get("/incidents/{incident_id}", response_model=dict)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir un incident avec ses commentaires (admin uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    
    db.refresh(incident, ['service_instance', 'service_instances', 'updates', 'comments'])
    
    # Récupérer les équipements via la table de liaison ou service_instance pour rétrocompatibilité
    service_instance_names = []
    service_instance_ids = []
    if incident.service_instances and len(incident.service_instances) > 0:
        service_instance_names = [si.name for si in incident.service_instances]
        service_instance_ids = [si.id for si in incident.service_instances]
    elif incident.service_instance:
        service_instance_names = [incident.service_instance.name]
        service_instance_ids = [incident.service_instance_id]
    
    # Charger les commentaires avec les infos des admins
    comments = []
    for comment in incident.comments:
        db.refresh(comment, ['admin'])
        comments.append({
            "id": comment.id,
            "comment": comment.comment,
            "admin_id": comment.admin_id,
            "admin_email": comment.admin.email if comment.admin else None,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        })
    
    return {
        "id": incident.id,
        "title": incident.title,
        "message": incident.message,
        "status": incident.status.value,
        "service_instance": ", ".join(service_instance_names) if service_instance_names else None,
        "service_instance_id": incident.service_instance_id,  # Pour rétrocompatibilité
        "service_instance_ids": service_instance_ids,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "comments": comments,
        "updates": [{"id": u.id, "message": u.message, "status": u.status.value, "created_at": u.created_at.isoformat()} for u in incident.updates]
    }


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: int,
    status_update: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour le statut d'un incident (admin uniquement)"""
    try:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident non trouvé")
        
        # Convertir le statut string en enum
        try:
            new_status = IncidentStatus(status_update.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Statut invalide: {status_update.status}. Valeurs acceptées: investigating, in_progress, resolved, closed"
            )
        
        # Si le statut est le même, ne rien faire
        if incident.status == new_status:
            return {"message": "Statut déjà à cette valeur", "incident_id": incident.id, "status": new_status.value}
        
        # Validation des transitions de statut
        # Permettre toutes les transitions sauf depuis CLOSED
        current_status = incident.status
        
        # Permettre la modification même si l'incident est clos
        
        # Pour les autres statuts, on permet toutes les transitions valides
        valid_transitions = {
            IncidentStatus.INVESTIGATING: [IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
            IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED, IncidentStatus.CLOSED, IncidentStatus.INVESTIGATING],
            IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.IN_PROGRESS],
            IncidentStatus.SCHEDULED: [IncidentStatus.INVESTIGATING, IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
        }
        
        # Si la transition n'est pas dans la liste, on l'autorise quand même (sauf depuis CLOSED)
        allowed_statuses = valid_transitions.get(current_status, [
            IncidentStatus.INVESTIGATING,
            IncidentStatus.IN_PROGRESS,
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED
        ])
        
        if new_status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Transition de statut invalide: {current_status.value} → {new_status.value}"
            )
        
        # Sauvegarder l'ancien statut pour le message
        old_status_value = current_status.value
        
        # Mettre à jour le statut
        incident.status = new_status
        if new_status == IncidentStatus.RESOLVED or new_status == IncidentStatus.CLOSED:
            if not incident.resolved_at:
                incident.resolved_at = datetime.utcnow()
        
        # Créer une mise à jour automatique seulement si le statut a changé
        update = IncidentUpdateModel(
            incident_id=incident_id,
            message=f"Statut changé: {old_status_value} → {new_status.value}",
            status=new_status
        )
        db.add(update)
        
        db.commit()
        db.refresh(incident)
        
        return {"message": "Statut mis à jour", "incident_id": incident.id, "status": new_status.value}
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erreur lors de la mise à jour du statut de l'incident: {e}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour du statut: {str(e)}"
        )


@router.put("/incidents/{incident_id}", response_model=dict)
async def update_incident(
    incident_id: int,
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour un incident (titre, description, équipement) (admin uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    
    # Mettre à jour le titre si fourni
    if incident_update.title is not None:
        incident.title = incident_update.title
    
    # Mettre à jour le message si fourni
    if incident_update.message is not None:
        incident.message = incident_update.message
    
    # Mettre à jour l'équipement si fourni
    if incident_update.service_instance_id is not None:
        # Vérifier que l'équipement existe et appartient à la même copropriété
        service_instance = db.query(ServiceInstance).filter(
            ServiceInstance.id == incident_update.service_instance_id,
            ServiceInstance.copro_id == incident.copro_id
        ).first()
        if not service_instance:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        incident.service_instance_id = incident_update.service_instance_id
    
    # Mettre à jour la date de création si fournie
    if incident_update.created_at is not None:
        incident.created_at = incident_update.created_at
    
    # Mettre à jour la date de résolution si fournie
    if incident_update.resolved_at is not None:
        incident.resolved_at = incident_update.resolved_at
    
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    return {
        "message": "Incident mis à jour",
        "incident_id": incident.id,
        "title": incident.title,
        "message": incident.message,
        "service_instance_id": incident.service_instance_id
    }


@router.post("/incidents/{incident_id}/updates", status_code=status.HTTP_201_CREATED)
async def add_incident_update(
    incident_id: int,
    update_data: IncidentUpdateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Ajouter une mise à jour à un incident (admin uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    
    update = IncidentUpdateModel(
        incident_id=incident_id,
        message=update_data.message,
        status=IncidentStatus(update_data.status)
    )
    
    db.add(update)
    
    # Mettre à jour le statut de l'incident
    incident.status = IncidentStatus(update_data.status)
    if update_data.status == "resolved" or update_data.status == "closed":
        incident.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(update)
    
    return {"message": "Mise à jour ajoutée", "update_id": update.id}


@router.post("/incidents/{incident_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_incident_comment(
    incident_id: int,
    comment_data: IncidentCommentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Ajouter un commentaire à un incident (admin uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    
    comment = IncidentComment(
        incident_id=incident_id,
        admin_id=admin.id,
        comment=comment_data.comment
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment, ['admin'])
    
    return {
        "message": "Commentaire ajouté",
        "comment_id": comment.id,
        "comment": comment.comment,
        "admin_email": admin.email,
        "created_at": comment.created_at.isoformat() if comment.created_at else None
    }


# ============ Gestion des Administrateurs ============

@router.get("/admins", response_model=List[dict])
async def list_admins(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les administrateurs (admin uniquement)"""
    admins = db.query(User).filter(
        User.is_superuser == True,
        User.is_active == True
    ).order_by(User.email).all()
    
    return [{"id": a.id, "email": a.email} for a in admins]


# ============ Gestion des Tickets ============

@router.get("/tickets", response_model=List[dict])
async def list_tickets(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les tickets (admin uniquement) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    query = db.query(Ticket).filter(Ticket.copro_id == copro.id)
    
    if status_filter:
        query = query.filter(Ticket.status == TicketStatus(status_filter))
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    result = []
    for ticket in tickets:
        db.refresh(ticket, ['service_instance', 'copro', 'assigned_admin', 'reviewer', 'incident', 'comments'])
        # Récupérer les commentaires
        comments = []
        for comment in ticket.comments:
            db.refresh(comment, ['admin'])
            comments.append({
                "id": comment.id,
                "comment": comment.comment,
                "admin_email": comment.admin.email if comment.admin else None,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
        
        result.append({
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "type": ticket.type.value if ticket.type else "incident",
            "status": ticket.status.value,
            "reporter_name": ticket.reporter_name,
            "reporter_email": ticket.reporter_email,
            "reporter_phone": ticket.reporter_phone,
            "location": ticket.location,
            "service_instance": ticket.service_instance.name if ticket.service_instance else None,
            "service_instance_id": ticket.service_instance_id,
            "copro": ticket.copro.name if ticket.copro else None,
            "assigned_to": ticket.assigned_to,
            "assigned_admin": ticket.assigned_admin.email if ticket.assigned_admin else None,
            "admin_notes": ticket.admin_notes,
            "reviewed_by": ticket.reviewed_by,
            "reviewer": ticket.reviewer.email if ticket.reviewer else None,
            "incident_id": ticket.incident_id,
            "comments": comments,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "reviewed_at": ticket.reviewed_at.isoformat() if ticket.reviewed_at else None,
        })
    
    return result


@router.patch("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Assigner un ticket à un administrateur (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Vérifier que l'utilisateur assigné est bien un admin
    assigned_user = db.query(User).filter(
        User.id == assign_data.assigned_to,
        User.is_superuser == True
    ).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Administrateur non trouvé")
    
    ticket.assigned_to = assign_data.assigned_to
    ticket.status = TicketStatus.ANALYZING
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ticket assigné", "ticket_id": ticket.id}


@router.post("/tickets/{ticket_id}/review")
async def review_ticket(
    ticket_id: int,
    review: TicketReview,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Analyser un ticket et décider de créer un incident ou non (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Mapper les anciens statuts vers les nouveaux si nécessaire
    if review.status == "approved":
        ticket.status = TicketStatus.IN_PROGRESS
    elif review.status == "rejected":
        ticket.status = TicketStatus.CLOSED
    else:
        try:
            ticket.status = TicketStatus(review.status)
        except ValueError:
            ticket.status = TicketStatus.ANALYZING
    
    if review.admin_notes:
        ticket.admin_notes = review.admin_notes
    ticket.reviewed_by = admin.id
    ticket.reviewed_at = datetime.utcnow()
    
    # Si approuvé et demande de création d'incident
    if (review.status == "approved" or ticket.status == TicketStatus.IN_PROGRESS) and review.create_incident:
        incident = Incident(
            copro_id=ticket.copro_id,
            service_instance_id=ticket.service_instance_id,
            title=ticket.title,
            message=ticket.description,
            status=IncidentStatus.INVESTIGATING  # En cours d'analyse
        )
        db.add(incident)
        db.flush()
        
        ticket.incident_id = incident.id
        
        # Copier les commentaires du ticket vers l'incident
        for ticket_comment in ticket.comments:
            incident_comment = IncidentComment(
                incident_id=incident.id,
                admin_id=ticket_comment.admin_id,
                comment=f"[Depuis ticket #{ticket.id}] {ticket_comment.comment}"
            )
            db.add(incident_comment)
        
        # Mettre à jour le statut du service si spécifié
        if ticket.service_instance_id:
            service_instance = db.query(ServiceInstance).filter(
                ServiceInstance.id == ticket.service_instance_id
            ).first()
            if service_instance:
                service_instance.status = "degraded"
    
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ticket traité", "ticket_id": ticket.id}


@router.post("/tickets/{ticket_id}/reject")
async def reject_ticket(
    ticket_id: int,
    admin_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Rejeter un ticket (admin uniquement) - DEPRECATED, utiliser update_status"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    ticket.status = TicketStatus.CLOSED
    if admin_notes:
        ticket.admin_notes = admin_notes
    ticket.reviewed_by = admin.id
    ticket.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ticket rejeté", "ticket_id": ticket.id}


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour le statut d'un ticket (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    try:
        ticket.status = TicketStatus(status_update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Statut mis à jour", "ticket_id": ticket.id, "status": ticket.status.value}


@router.post("/tickets/{ticket_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_ticket_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Ajouter un commentaire à un ticket (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    comment = TicketComment(
        ticket_id=ticket_id,
        admin_id=admin.id,
        comment=comment_data.comment
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment, ['admin'])
    
    return {
        "message": "Commentaire ajouté",
        "comment_id": comment.id,
        "comment": comment.comment,
        "admin_email": admin.email,
        "created_at": comment.created_at.isoformat() if comment.created_at else None
    }


@router.get("/tickets/{ticket_id}/comments")
async def get_ticket_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Récupérer les commentaires d'un ticket (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    comments = db.query(TicketComment).filter(
        TicketComment.ticket_id == ticket_id
    ).order_by(TicketComment.created_at).all()
    
    result = []
    for comment in comments:
        db.refresh(comment, ['admin'])
        result.append({
            "id": comment.id,
            "comment": comment.comment,
            "admin_email": comment.admin.email if comment.admin else None,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        })
    
    return result


# ============ Gestion des Utilisateurs ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    lot_number: Optional[str] = None
    floor: Optional[str] = None
    building_id: Optional[int] = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    lot_number: Optional[str] = None
    floor: Optional[str] = None
    building_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    lot_number: Optional[str] = None
    floor: Optional[str] = None
    building_id: Optional[int] = None
    building_name: Optional[str] = None
    building_identifier: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les utilisateurs (admin uniquement)"""
    users = db.query(User).all()
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "lot_number": user.lot_number,
            "floor": user.floor,
            "building_id": user.building_id,
            "building_name": None,
            "building_identifier": None,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at
        }
        if user.building:
            user_dict["building_name"] = user.building.name
            user_dict["building_identifier"] = user.building.name
        result.append(user_dict)
    return result


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Récupérer un utilisateur par ID (admin uniquement)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user_dict = {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "lot_number": user.lot_number,
        "floor": user.floor,
        "building_id": user.building_id,
        "building_name": None,
        "building_identifier": None,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at
    }
    if user.building:
        user_dict["building_name"] = user.building.name
        user_dict["building_identifier"] = user.building.name
    return user_dict


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer un nouvel utilisateur (admin uniquement)"""
    # Vérifier que l'email n'existe pas déjà
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Cet email existe déjà")
    
    # Vérifier le bâtiment si fourni
    if user_data.building_id:
        building = db.query(Building).filter(Building.id == user_data.building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Récupérer la copropriété active
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Créer l'utilisateur
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        lot_number=user_data.lot_number,
        floor=user_data.floor,
        building_id=user_data.building_id,
        copro_id=copro.id,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    user_dict = {
        "id": new_user.id,
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "lot_number": new_user.lot_number,
        "floor": new_user.floor,
        "building_id": new_user.building_id,
        "building_name": None,
        "building_identifier": None,
        "is_active": new_user.is_active,
        "is_superuser": new_user.is_superuser,
        "created_at": new_user.created_at
    }
    if new_user.building:
        user_dict["building_name"] = new_user.building.name
        user_dict["building_identifier"] = new_user.building.name
    
    return user_dict


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour un utilisateur (admin uniquement)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Vérifier que l'email n'existe pas déjà (si modifié)
    if user_data.email and user_data.email != user.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Cet email existe déjà")
        user.email = user_data.email
    
    # Mettre à jour le mot de passe si fourni
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    
    # Vérifier le bâtiment si fourni
    if user_data.building_id is not None:
        if user_data.building_id:
            building = db.query(Building).filter(Building.id == user_data.building_id).first()
            if not building:
                raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
        user.building_id = user_data.building_id
    
    # Mettre à jour les autres champs
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.lot_number is not None:
        user.lot_number = user_data.lot_number
    if user_data.floor is not None:
        user.floor = user_data.floor
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    
    db.commit()
    db.refresh(user)
    
    user_dict = {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "lot_number": user.lot_number,
        "floor": user.floor,
        "building_id": user.building_id,
        "building_name": None,
        "building_identifier": None,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at
    }
    if user.building:
        user_dict["building_name"] = user.building.name
        user_dict["building_identifier"] = user.building.name
    
    return user_dict


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Supprimer un utilisateur (admin uniquement)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Empêcher la suppression de soi-même
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    
    db.delete(user)
    db.commit()
    
    return {"message": "Utilisateur supprimé"}


# ============ Gestion des Maintenances ============

class MaintenanceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    service_instance_ids: List[int]  # Liste des IDs des équipements concernés


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    service_instance_ids: Optional[List[int]] = None


class MaintenanceResponse(BaseModel):
    id: int
    copro_id: int
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    service_instances: List[dict]  # Liste des équipements concernés

    class Config:
        from_attributes = True


@router.get("/maintenances", response_model=List[MaintenanceResponse])
async def list_maintenances(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister toutes les maintenances (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    maintenances = db.query(Maintenance).filter(
        Maintenance.copro_id == copro.id
    ).order_by(Maintenance.start_date.desc()).all()
    
    result = []
    for maintenance in maintenances:
        db.refresh(maintenance, ['service_instances'])
        result.append(MaintenanceResponse(
            id=maintenance.id,
            copro_id=maintenance.copro_id,
            title=maintenance.title,
            description=maintenance.description,
            start_date=maintenance.start_date,
            end_date=maintenance.end_date,
            created_at=maintenance.created_at,
            updated_at=maintenance.updated_at,
            service_instances=[
                {
                    "id": si.id,
                    "name": si.name,
                    "building_name": si.building.name if si.building else None
                }
                for si in maintenance.service_instances
            ]
        ))
    
    return result


@router.get("/maintenances/{maintenance_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir une maintenance par ID (admin uniquement)"""
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance non trouvée")
    
    db.refresh(maintenance, ['service_instances'])
    return MaintenanceResponse(
        id=maintenance.id,
        copro_id=maintenance.copro_id,
        title=maintenance.title,
        description=maintenance.description,
        start_date=maintenance.start_date,
        end_date=maintenance.end_date,
        created_at=maintenance.created_at,
        updated_at=maintenance.updated_at,
        service_instances=[
            {
                "id": si.id,
                "name": si.name,
                "building_name": si.building.name if si.building else None
            }
            for si in maintenance.service_instances
        ]
    )


@router.post("/maintenances", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Créer une nouvelle maintenance (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Vérifier que la date de fin est après la date de début
    if maintenance_data.end_date <= maintenance_data.start_date:
        raise HTTPException(status_code=400, detail="La date de fin doit être après la date de début")
    
    # Vérifier que les équipements existent et appartiennent à la copropriété
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.id.in_(maintenance_data.service_instance_ids),
        ServiceInstance.copro_id == copro.id
    ).all()
    
    if len(service_instances) != len(maintenance_data.service_instance_ids):
        raise HTTPException(status_code=404, detail="Un ou plusieurs équipements non trouvés")
    
    # Créer la maintenance
    maintenance = Maintenance(
        copro_id=copro.id,
        title=maintenance_data.title,
        description=maintenance_data.description,
        start_date=maintenance_data.start_date,
        end_date=maintenance_data.end_date
    )
    db.add(maintenance)
    db.flush()
    
    # Associer les équipements
    maintenance.service_instances = service_instances
    db.commit()
    db.refresh(maintenance, ['service_instances'])
    
    return MaintenanceResponse(
        id=maintenance.id,
        copro_id=maintenance.copro_id,
        title=maintenance.title,
        description=maintenance.description,
        start_date=maintenance.start_date,
        end_date=maintenance.end_date,
        created_at=maintenance.created_at,
        updated_at=maintenance.updated_at,
        service_instances=[
            {
                "id": si.id,
                "name": si.name,
                "building_name": si.building.name if si.building else None
            }
            for si in maintenance.service_instances
        ]
    )


@router.put("/maintenances/{maintenance_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    maintenance_id: int,
    maintenance_update: MaintenanceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Mettre à jour une maintenance (admin uniquement)"""
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance non trouvée")
    
    update_data = maintenance_update.dict(exclude_unset=True)
    
    # Vérifier les dates si fournies
    start_date = update_data.get('start_date', maintenance.start_date)
    end_date = update_data.get('end_date', maintenance.end_date)
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="La date de fin doit être après la date de début")
    
    # Mettre à jour les champs
    if 'title' in update_data:
        maintenance.title = update_data['title']
    if 'description' in update_data:
        maintenance.description = update_data['description']
    if 'start_date' in update_data:
        maintenance.start_date = update_data['start_date']
    if 'end_date' in update_data:
        maintenance.end_date = update_data['end_date']
    
    # Mettre à jour les équipements si fournis
    if 'service_instance_ids' in update_data:
        copro = db.query(Copro).filter(Copro.id == maintenance.copro_id).first()
        service_instances = db.query(ServiceInstance).filter(
            ServiceInstance.id.in_(update_data['service_instance_ids']),
            ServiceInstance.copro_id == copro.id
        ).all()
        
        if len(service_instances) != len(update_data['service_instance_ids']):
            raise HTTPException(status_code=404, detail="Un ou plusieurs équipements non trouvés")
        
        maintenance.service_instances = service_instances
    
    maintenance.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(maintenance, ['service_instances'])
    
    return MaintenanceResponse(
        id=maintenance.id,
        copro_id=maintenance.copro_id,
        title=maintenance.title,
        description=maintenance.description,
        start_date=maintenance.start_date,
        end_date=maintenance.end_date,
        created_at=maintenance.created_at,
        updated_at=maintenance.updated_at,
        service_instances=[
            {
                "id": si.id,
                "name": si.name,
                "building_name": si.building.name if si.building else None
            }
            for si in maintenance.service_instances
        ]
    )


@router.delete("/maintenances/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Supprimer une maintenance (admin uniquement)"""
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance non trouvée")
    
    db.delete(maintenance)
    db.commit()
    return None


# ============ Statistiques ============

@router.get("/statistics/general", response_model=dict)
async def get_general_statistics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir les statistiques générales des incidents (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return {
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": []
        }
    
    # Date de début (6 mois en arrière)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Nombre d'incidents par jour sur les 6 derniers mois
    incidents_by_day_query = db.query(
        sql_func.date(Incident.created_at).label('date'),
        sql_func.count(Incident.id).label('count')
    ).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.created_at >= six_months_ago
        )
    ).group_by(
        sql_func.date(Incident.created_at)
    ).order_by(
        sql_func.date(Incident.created_at)
    ).all()
    
    incidents_by_day = [
        {
            "date": row.date.isoformat() if row.date else None,
            "count": row.count
        }
        for row in incidents_by_day_query
    ]
    
    # Tous les incidents
    all_incidents_query = db.query(Incident).filter(
        Incident.copro_id == copro.id
    ).order_by(Incident.created_at.desc()).all()
    
    all_incidents = []
    for incident in all_incidents_query:
        db.refresh(incident, ['service_instance'])
        resolution_time = None
        if incident.resolved_at and incident.created_at:
            delta = incident.resolved_at - incident.created_at
            resolution_time = delta.total_seconds() / 3600  # En heures
        
        all_incidents.append({
            "id": incident.id,
            "title": incident.title,
            "message": incident.message,
            "status": incident.status.value,
            "service_instance": incident.service_instance.name if incident.service_instance else None,
            "service_instance_id": incident.service_instance_id,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "resolution_time_hours": resolution_time
        })
    
    # Temps de résolution par équipement (moyen, min, max)
    resolution_stats_query = db.query(
        ServiceInstance.id,
        ServiceInstance.name,
        sql_func.avg(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('avg_hours'),
        sql_func.min(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('min_hours'),
        sql_func.max(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('max_hours'),
        sql_func.count(Incident.id).label('incident_count')
    ).join(
        Incident, ServiceInstance.id == Incident.service_instance_id
    ).filter(
        and_(
            ServiceInstance.copro_id == copro.id,
            Incident.copro_id == copro.id,
            Incident.resolved_at.isnot(None)
        )
    ).group_by(
        ServiceInstance.id,
        ServiceInstance.name
    ).all()
    
    resolution_time_by_equipment = [
        {
            "equipment_id": row.id,
            "equipment_name": row.name,
            "avg_hours": float(row.avg_hours) if row.avg_hours else None,
            "min_hours": float(row.min_hours) if row.min_hours else None,
            "max_hours": float(row.max_hours) if row.max_hours else None,
            "incident_count": row.incident_count
        }
        for row in resolution_stats_query
    ]
    
    return {
        "incidents_by_day": incidents_by_day,
        "all_incidents": all_incidents,
        "resolution_time_by_equipment": resolution_time_by_equipment
    }


@router.get("/statistics/by-building/{building_id}", response_model=dict)
async def get_statistics_by_building(
    building_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Obtenir les statistiques des incidents par bâtiment (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return {
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": []
        }
    
    # Vérifier que le bâtiment existe et appartient à la copropriété
    building = db.query(Building).filter(
        Building.id == building_id,
        Building.copro_id == copro.id
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Date de début (6 mois en arrière)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Récupérer les IDs des équipements du bâtiment
    equipment_ids = [si.id for si in db.query(ServiceInstance.id).filter(
        ServiceInstance.building_id == building_id,
        ServiceInstance.copro_id == copro.id
    ).all()]
    
    if not equipment_ids:
        return {
            "building_id": building_id,
            "building_name": building.name,
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": []
        }
    
    # Nombre d'incidents par jour sur les 6 derniers mois pour ce bâtiment
    incidents_by_day_query = db.query(
        sql_func.date(Incident.created_at).label('date'),
        sql_func.count(Incident.id).label('count')
    ).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.created_at >= six_months_ago,
            Incident.service_instance_id.in_(equipment_ids)
        )
    ).group_by(
        sql_func.date(Incident.created_at)
    ).order_by(
        sql_func.date(Incident.created_at)
    ).all()
    
    incidents_by_day = [
        {
            "date": row.date.isoformat() if row.date else None,
            "count": row.count
        }
        for row in incidents_by_day_query
    ]
    
    # Tous les incidents pour ce bâtiment
    all_incidents_query = db.query(Incident).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.service_instance_id.in_(equipment_ids)
        )
    ).order_by(Incident.created_at.desc()).all()
    
    all_incidents = []
    for incident in all_incidents_query:
        db.refresh(incident, ['service_instance'])
        resolution_time = None
        if incident.resolved_at and incident.created_at:
            delta = incident.resolved_at - incident.created_at
            resolution_time = delta.total_seconds() / 3600  # En heures
        
        all_incidents.append({
            "id": incident.id,
            "title": incident.title,
            "message": incident.message,
            "status": incident.status.value,
            "service_instance": incident.service_instance.name if incident.service_instance else None,
            "service_instance_id": incident.service_instance_id,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "resolution_time_hours": resolution_time
        })
    
    # Temps de résolution par équipement (moyen, min, max) pour ce bâtiment
    resolution_stats_query = db.query(
        ServiceInstance.id,
        ServiceInstance.name,
        sql_func.avg(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('avg_hours'),
        sql_func.min(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('min_hours'),
        sql_func.max(
            sql_func.extract('epoch', Incident.resolved_at - Incident.created_at) / 3600
        ).label('max_hours'),
        sql_func.count(Incident.id).label('incident_count')
    ).join(
        Incident, ServiceInstance.id == Incident.service_instance_id
    ).filter(
        and_(
            ServiceInstance.copro_id == copro.id,
            ServiceInstance.building_id == building_id,
            Incident.copro_id == copro.id,
            Incident.resolved_at.isnot(None)
        )
    ).group_by(
        ServiceInstance.id,
        ServiceInstance.name
    ).all()
    
    resolution_time_by_equipment = [
        {
            "equipment_id": row.id,
            "equipment_name": row.name,
            "avg_hours": float(row.avg_hours) if row.avg_hours else None,
            "min_hours": float(row.min_hours) if row.min_hours else None,
            "max_hours": float(row.max_hours) if row.max_hours else None,
            "incident_count": row.incident_count
        }
        for row in resolution_stats_query
    ]
    
    return {
        "building_id": building_id,
        "building_name": building.name,
        "incidents_by_day": incidents_by_day,
        "all_incidents": all_incidents,
        "resolution_time_by_equipment": resolution_time_by_equipment
    }
