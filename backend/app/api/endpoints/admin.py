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
from app.models.status import Incident, IncidentUpdate, IncidentStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from app.auth import get_current_user

router = APIRouter()


# ============ Schemas ============

class ServiceInstanceStatusUpdate(BaseModel):
    status: str  # operational, degraded, partial_outage, major_outage, maintenance


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
    building_name: str
    service_type_name: str

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
            building_name=instance.building.name if instance.building else "",
            service_type_name=instance.service_type.name if instance.service_type else ""
        ))
    
    return result


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
    if update_data.status == "resolved":
        incident.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(update)
    
    return {"message": "Mise à jour ajoutée", "update_id": update.id}


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
        db.refresh(ticket, ['service_instance', 'copro'])
        result.append({
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status.value,
            "reporter_name": ticket.reporter_name,
            "reporter_email": ticket.reporter_email,
            "service_instance": ticket.service_instance.name if ticket.service_instance else None,
            "copro": ticket.copro.name if ticket.copro else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "reviewed_at": ticket.reviewed_at.isoformat() if ticket.reviewed_at else None,
        })
    
    return result


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
            status=IncidentStatus.INVESTIGATING
        )
        db.add(incident)
        db.flush()
        
        ticket.incident_id = incident.id
        
        # Optionnel: mettre à jour le statut du service si spécifié
        if ticket.service_instance_id:
            service_instance = db.query(ServiceInstance).filter(
                ServiceInstance.id == ticket.service_instance_id
            ).first()
            if service_instance:
                service_instance.status = "degraded"  # Ou un autre statut approprié
    
    db.commit()
    db.refresh(ticket)
    
    return {"message": "Ticket traité", "ticket_id": ticket.id}

