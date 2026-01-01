"""
API endpoints publics (sans authentification)
- Déclaration de tickets d'incident
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.copro import Copro, ServiceInstance, Building
from typing import List

router = APIRouter()


class TicketCreate(BaseModel):
    service_instance_id: Optional[int] = None
    reporter_name: Optional[str] = None
    reporter_email: Optional[EmailStr] = None
    reporter_phone: Optional[str] = None
    title: str
    description: str
    location: Optional[str] = None


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """Créer un ticket de déclaration d'incident (public) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Vérifier que le service_instance existe (si spécifié)
    if ticket_data.service_instance_id:
        service_instance = db.query(ServiceInstance).filter(
            ServiceInstance.id == ticket_data.service_instance_id,
            ServiceInstance.copro_id == copro.id
        ).first()
        if not service_instance:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
    
    ticket = Ticket(
        copro_id=copro.id,
        service_instance_id=ticket_data.service_instance_id,
        reporter_name=ticket_data.reporter_name,
        reporter_email=ticket_data.reporter_email,
        reporter_phone=ticket_data.reporter_phone,
        title=ticket_data.title,
        description=ticket_data.description,
        location=ticket_data.location,
        status=TicketStatus.PENDING
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Ticket créé avec succès",
        "ticket_id": ticket.id,
        "status": ticket.status.value
    }


@router.get("/service-instances")
async def get_public_service_instances(db: Session = Depends(get_db)):
    """Obtenir la liste des équipements (public, pour le formulaire) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.is_active == True
    ).order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    result = []
    for instance in service_instances:
        db.refresh(instance, ['building'])
        result.append({
            "id": instance.id,
            "name": instance.name,
            "building": instance.building.name if instance.building else "",
            "status": instance.status
        })
    
    return result


@router.get("/buildings")
async def get_public_buildings(db: Session = Depends(get_db)):
    """Obtenir la liste des bâtiments (public, pour le formulaire d'inscription) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return []
    
    buildings = db.query(Building).filter(
        Building.copro_id == copro.id,
        Building.is_active == True
    ).order_by(Building.order, Building.name).all()
    
    result = []
    for building in buildings:
        result.append({
            "id": building.id,
            "name": building.name
        })
    
    return result

