"""
API endpoints publics (sans authentification)
- Déclaration de tickets d'incident
"""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db import get_db
from app.models.ticket import Ticket, TicketStatus, TicketType
from app.models.copro import Copro, ServiceInstance, Building
from typing import List

router = APIRouter()


class TicketCreate(BaseModel):
    service_instance_id: Optional[int] = None
    reporter_name: str
    reporter_email: EmailStr
    reporter_phone: str
    title: str
    description: str
    location: Optional[str] = None
    type: str = "incident"  # "incident" ou "request"


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """Créer un ticket de déclaration d'incident (public) - Une seule copropriété"""
    try:
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
        
        # Valider le type
        if ticket_data.type not in ["incident", "request"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le type doit être 'incident' ou 'request'"
            )
        # Convertir la valeur string en enum (les valeurs sont en minuscules mais l'enum PostgreSQL utilise les noms en majuscules)
        if ticket_data.type == "incident":
            ticket_type = TicketType.INCIDENT
        elif ticket_data.type == "request":
            ticket_type = TicketType.REQUEST
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le type doit être 'incident' ou 'request'"
            )
        
        # Validation de l'équipement (obligatoire seulement pour les incidents)
        if ticket_data.type == "incident" and not ticket_data.service_instance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'équipement concerné est obligatoire pour un incident"
            )
        
        # Validation supplémentaire des champs
        if not ticket_data.title or len(ticket_data.title.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le titre doit contenir au moins 3 caractères"
            )
        
        if not ticket_data.description or len(ticket_data.description.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La description doit contenir au moins 10 caractères"
            )
        
        # Validation de la localisation (optionnelle, mais si remplie, doit avoir au moins 3 caractères)
        if ticket_data.location is not None and ticket_data.location.strip() and len(ticket_data.location.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La localisation doit contenir au moins 3 caractères si renseignée"
            )
        
        if not ticket_data.reporter_name or len(ticket_data.reporter_name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nom doit contenir au moins 2 caractères"
            )
        
        # Validation du téléphone (format français)
        clean_phone = re.sub(r'[\s\-\.]', '', ticket_data.reporter_phone)
        if not re.match(r'^0[1-9][0-9]{8}$', clean_phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le numéro de téléphone doit être un numéro français valide (10 chiffres, exemple: 0612345678)"
            )
        
        ticket = Ticket(
            copro_id=copro.id,
            service_instance_id=ticket_data.service_instance_id,
            reporter_name=ticket_data.reporter_name.strip(),
            reporter_email=ticket_data.reporter_email.strip(),
            reporter_phone=clean_phone,  # Utiliser le numéro nettoyé
            title=ticket_data.title.strip(),
            description=ticket_data.description.strip(),
            location=ticket_data.location.strip() if ticket_data.location else None,
            type=ticket_type,
            status=TicketStatus.ANALYZING
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        return {
            "message": "Ticket créé avec succès",
            "ticket_id": ticket.id,
            "status": ticket.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du ticket: {str(e)}"
        )


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

