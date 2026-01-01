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
from pydantic import BaseModel
from datetime import datetime
from app.db import get_db
from app.models.copro import Copro, Building, ServiceType, ServiceInstance
from app.models.status import Incident, IncidentUpdate, IncidentComment, IncidentStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class ServiceInstanceStatusUpdate(BaseModel):
    status: str  # operational, degraded, partial_outage, major_outage, maintenance


class ServiceInstanceCreate(BaseModel):
    building_id: int
    service_type_id: int
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: str = "operational"
    order: int = 0


class ServiceInstanceUpdate(BaseModel):
    building_id: Optional[int] = None
    service_type_id: Optional[int] = None
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
    service_type_id: int
    name: str
    identifier: Optional[str]
    description: Optional[str]
    location: Optional[str]
    status: str
    is_active: bool
    order: int
    building_name: str
    service_type_name: str
    building_identifier: str

    class Config:
        from_attributes = True


class IncidentCreate(BaseModel):
    service_instance_id: Optional[int] = None
    title: str
    message: str
    status: str = "investigating"
    is_scheduled: bool = False
    scheduled_for: Optional[datetime] = None


class IncidentUpdateCreate(BaseModel):
    message: str
    status: str


class TicketReview(BaseModel):
    status: str  # approved, rejected
    admin_notes: Optional[str] = None
    create_incident: bool = False  # Si True, créer un incident automatiquement


class TicketAssign(BaseModel):
    assigned_to: int  # ID de l'administrateur


class IncidentStatusUpdate(BaseModel):
    status: str  # investigating, in_progress, resolved, closed


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


def create_default_service_types(copro_id: int, db: Session):
    """Créer les types de services par défaut pour une copropriété"""
    default_service_types = [
        {
            "name": "Ascenseur",
            "description": "Ascenseur de l'immeuble",
            "category": "Équipement",
            "order": 1
        },
        {
            "name": "Éclairage",
            "description": "Éclairage des parties communes",
            "category": "Équipement",
            "order": 2
        },
        {
            "name": "Eau chaude",
            "description": "Production d'eau chaude sanitaire",
            "category": "Fluide",
            "order": 3
        },
        {
            "name": "Eau froide",
            "description": "Distribution d'eau froide",
            "category": "Fluide",
            "order": 4
        },
        {
            "name": "Porte parking",
            "description": "Porte d'accès au parking",
            "category": "Sécurité",
            "order": 5
        },
    ]
    
    for st_data in default_service_types:
        # Vérifier si le type existe déjà
        existing = db.query(ServiceType).filter(
            ServiceType.copro_id == copro_id,
            ServiceType.name == st_data["name"]
        ).first()
        
        if not existing:
            service_type = ServiceType(
                copro_id=copro_id,
                name=st_data["name"],
                description=st_data["description"],
                category=st_data["category"],
                default_status="operational",
                order=st_data["order"],
                is_active=True
            )
            db.add(service_type)
    
    db.commit()


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
    
    # Créer les types de services par défaut
    create_default_service_types(db_copro.id, db)
    
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
    identifier: str
    name: Optional[str] = None
    description: Optional[str] = None
    order: int = 0


class BuildingUpdate(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class BuildingResponse(BaseModel):
    id: int
    copro_id: int
    identifier: str
    name: Optional[str]
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
    ).order_by(Building.order, Building.identifier).all()
    
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
    
    # Vérifier l'unicité de l'identifiant dans la copropriété
    existing = db.query(Building).filter(
        Building.copro_id == copro.id,
        Building.identifier == building.identifier
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un bâtiment avec l'identifiant '{building.identifier}' existe déjà")
    
    db_building = Building(
        copro_id=copro.id,
        identifier=building.identifier,
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
    
    # Vérifier l'unicité de l'identifiant si modifié
    if 'identifier' in update_data and update_data['identifier'] != building.identifier:
        existing = db.query(Building).filter(
            Building.copro_id == building.copro_id,
            Building.identifier == update_data['identifier'],
            Building.id != building_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Un bâtiment avec l'identifiant '{update_data['identifier']}' existe déjà")
    
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


@router.get("/service-types", response_model=List[dict])
async def list_service_types(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Lister tous les types de services (admin uniquement)"""
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    # S'assurer que les types de services par défaut existent
    service_types_count = db.query(ServiceType).filter(
        ServiceType.copro_id == copro.id,
        ServiceType.is_active == True
    ).count()
    
    if service_types_count == 0:
        # Créer les types de services par défaut s'ils n'existent pas
        create_default_service_types(copro.id, db)
    
    service_types = db.query(ServiceType).filter(
        ServiceType.copro_id == copro.id,
        ServiceType.is_active == True
    ).order_by(ServiceType.order, ServiceType.name).all()
    
    return [{"id": st.id, "name": st.name, "category": st.category} for st in service_types]


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
        db.refresh(instance, ['building', 'service_type'])
        result.append(ServiceInstanceResponse(
            id=instance.id,
            copro_id=instance.copro_id,
            building_id=instance.building_id,
            service_type_id=instance.service_type_id,
            name=instance.name,
            identifier=instance.identifier,
            description=instance.description,
            location=instance.location,
            status=instance.status,
            is_active=instance.is_active,
            order=instance.order,
            building_name=instance.building.name if instance.building else "",
            service_type_name=instance.service_type.name if instance.service_type else "",
            building_identifier=instance.building.identifier if instance.building else ""
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
    
    db.refresh(instance, ['building', 'service_type'])
    return ServiceInstanceResponse(
        id=instance.id,
        copro_id=instance.copro_id,
        building_id=instance.building_id,
        service_type_id=instance.service_type_id,
        name=instance.name,
        identifier=instance.identifier,
        description=instance.description,
        location=instance.location,
        status=instance.status,
        is_active=instance.is_active,
        order=instance.order,
        building_name=instance.building.name if instance.building else "",
        service_type_name=instance.service_type.name if instance.service_type else "",
        building_identifier=instance.building.identifier if instance.building else ""
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
    
    # Vérifier que le type de service existe et appartient à la copropriété
    service_type = db.query(ServiceType).filter(
        ServiceType.id == service_instance.service_type_id,
        ServiceType.copro_id == copro.id
    ).first()
    if not service_type:
        raise HTTPException(status_code=404, detail="Type de service non trouvé")
    
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
        service_type_id=service_instance.service_type_id,
        name=service_instance.name,
        identifier=service_instance.identifier,
        description=service_instance.description,
        location=service_instance.location,
        status=service_instance.status,
        order=service_instance.order
    )
    
    db.add(db_service_instance)
    db.commit()
    db.refresh(db_service_instance, ['building', 'service_type'])
    
    return ServiceInstanceResponse(
        id=db_service_instance.id,
        copro_id=db_service_instance.copro_id,
        building_id=db_service_instance.building_id,
        service_type_id=db_service_instance.service_type_id,
        name=db_service_instance.name,
        identifier=db_service_instance.identifier,
        description=db_service_instance.description,
        location=db_service_instance.location,
        status=db_service_instance.status,
        is_active=db_service_instance.is_active,
        order=db_service_instance.order,
        building_name=db_service_instance.building.name if db_service_instance.building else "",
        service_type_name=db_service_instance.service_type.name if db_service_instance.service_type else "",
        building_identifier=db_service_instance.building.identifier if db_service_instance.building else ""
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
    
    # Vérifier le type de service si fourni
    if 'service_type_id' in update_data:
        service_type = db.query(ServiceType).filter(
            ServiceType.id == update_data['service_type_id'],
            ServiceType.copro_id == instance.copro_id
        ).first()
        if not service_type:
            raise HTTPException(status_code=404, detail="Type de service non trouvé")
    
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
    db.refresh(instance, ['building', 'service_type'])
    
    return ServiceInstanceResponse(
        id=instance.id,
        copro_id=instance.copro_id,
        building_id=instance.building_id,
        service_type_id=instance.service_type_id,
        name=instance.name,
        identifier=instance.identifier,
        description=instance.description,
        location=instance.location,
        status=instance.status,
        is_active=instance.is_active,
        order=instance.order,
        building_name=instance.building.name if instance.building else "",
        service_type_name=instance.service_type.name if instance.service_type else "",
        building_identifier=instance.building.identifier if instance.building else ""
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
    """Créer un incident (admin uniquement)"""
    copro_id = None
    
    # Si un service_instance est spécifié, récupérer la copropriété
    if incident_data.service_instance_id:
        service_instance = db.query(ServiceInstance).filter(
            ServiceInstance.id == incident_data.service_instance_id
        ).first()
        if not service_instance:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        copro_id = service_instance.copro_id
    
    incident = Incident(
        copro_id=copro_id,
        service_instance_id=incident_data.service_instance_id,
        title=incident_data.title,
        message=incident_data.message,
        status=IncidentStatus(incident_data.status),
        is_scheduled=incident_data.is_scheduled,
        scheduled_for=incident_data.scheduled_for
    )
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
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
        db.refresh(incident, ['service_instance'])
        result.append({
            "id": incident.id,
            "title": incident.title,
            "message": incident.message,
            "status": incident.status.value,
            "service_instance": incident.service_instance.name if incident.service_instance else None,
            "service_instance_id": incident.service_instance_id,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
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
    
    db.refresh(incident, ['service_instance', 'updates', 'comments'])
    
    # Charger les commentaires avec les infos des admins
    comments = []
    for comment in incident.comments:
        db.refresh(comment, ['admin'])
        comments.append({
            "id": comment.id,
            "comment": comment.comment,
            "admin_id": comment.admin_id,
            "admin_username": comment.admin.username if comment.admin else None,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        })
    
    return {
        "id": incident.id,
        "title": incident.title,
        "message": incident.message,
        "status": incident.status.value,
        "service_instance": incident.service_instance.name if incident.service_instance else None,
        "service_instance_id": incident.service_instance_id,
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
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    
    new_status = IncidentStatus(status_update.status)
    
    # Validation des transitions de statut
    valid_transitions = {
        IncidentStatus.INVESTIGATING: [IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
        IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
        IncidentStatus.RESOLVED: [IncidentStatus.CLOSED],
        IncidentStatus.CLOSED: []  # Une fois clos, on ne peut plus changer
    }
    
    if new_status not in valid_transitions.get(incident.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transition de statut invalide: {incident.status.value} → {new_status.value}"
        )
    
    # Mettre à jour le statut
    incident.status = new_status
    if new_status == IncidentStatus.RESOLVED or new_status == IncidentStatus.CLOSED:
        incident.resolved_at = datetime.utcnow()
    
    # Créer une mise à jour automatique
    update = IncidentUpdate(
        incident_id=incident_id,
        message=f"Statut changé: {incident.status.value} → {new_status.value}",
        status=new_status
    )
    db.add(update)
    
    db.commit()
    db.refresh(incident)
    
    return {"message": "Statut mis à jour", "incident_id": incident.id, "status": new_status.value}


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
    
    update = IncidentUpdate(
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
        "admin_username": admin.username,
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
    ).order_by(User.username).all()
    
    return [{"id": a.id, "username": a.username, "email": a.email} for a in admins]


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
        db.refresh(ticket, ['service_instance', 'copro', 'assigned_admin', 'reviewer', 'incident'])
        result.append({
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status.value,
            "reporter_name": ticket.reporter_name,
            "reporter_email": ticket.reporter_email,
            "reporter_phone": ticket.reporter_phone,
            "location": ticket.location,
            "service_instance": ticket.service_instance.name if ticket.service_instance else None,
            "service_instance_id": ticket.service_instance_id,
            "copro": ticket.copro.name if ticket.copro else None,
            "assigned_to": ticket.assigned_to,
            "assigned_admin": ticket.assigned_admin.username if ticket.assigned_admin else None,
            "admin_notes": ticket.admin_notes,
            "reviewed_by": ticket.reviewed_by,
            "reviewer": ticket.reviewer.username if ticket.reviewer else None,
            "incident_id": ticket.incident_id,
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
    ticket.status = TicketStatus.REVIEWING
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
    
    ticket.status = TicketStatus(review.status)
    ticket.admin_notes = review.admin_notes
    ticket.reviewed_by = admin.id
    ticket.reviewed_at = datetime.utcnow()
    
    # Si approuvé et demande de création d'incident
    if review.status == "approved" and review.create_incident:
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
    """Rejeter un ticket (admin uniquement)"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    ticket.status = TicketStatus.REJECTED
    ticket.admin_notes = admin_notes
    ticket.reviewed_by = admin.id
    ticket.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ticket rejeté", "ticket_id": ticket.id}

