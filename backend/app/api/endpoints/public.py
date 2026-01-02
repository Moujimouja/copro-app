"""
API endpoints publics (sans authentification)
- Déclaration de tickets d'incident
- Statistiques publiques
"""
import re
from calendar import isleap
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func as sql_func, and_
from app.db import get_db
from app.models.ticket import Ticket, TicketStatus, TicketType
from app.models.copro import Copro, ServiceInstance, Building
from app.models.status import Incident
from typing import List

router = APIRouter()


class TicketCreate(BaseModel):
    service_instance_id: Optional[int] = None
    reporter_name: str
    reporter_email: EmailStr
    reporter_phone: Optional[str] = None
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
        
        # Validation du téléphone (optionnel, mais si rempli, doit être valide)
        clean_phone = None
        if ticket_data.reporter_phone and ticket_data.reporter_phone.strip():
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
            reporter_phone=clean_phone,  # Utiliser le numéro nettoyé ou None
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


# ============ Statistiques publiques ============

@router.get("/statistics/general", response_model=dict)
async def get_public_general_statistics(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques générales des incidents (public, sans authentification)
    
    Args:
        year: Année pour laquelle calculer les statistiques (par défaut: année en cours)
    """
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return {
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": [],
            "equipment_availability": []
        }
    
    # Si aucune année n'est spécifiée, utiliser l'année en cours
    if year is None:
        year = datetime.utcnow().year
    
    # Dates de début et fin de l'année (1er janvier 00:00:00 au 31 décembre 23:59:59)
    start_date = datetime(year, 1, 1, 0, 0, 0)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    # Nombre d'incidents par jour sur l'année sélectionnée
    incidents_by_day_query = db.query(
        sql_func.date(Incident.created_at).label('date'),
        sql_func.count(Incident.id).label('count')
    ).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.created_at >= start_date,
            Incident.created_at <= end_date
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
    
    # Tous les incidents de l'année sélectionnée
    all_incidents_query = db.query(Incident).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.created_at >= start_date,
            Incident.created_at <= end_date
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
    
    # Calcul de la disponibilité par équipement
    # Période de référence : année complète
    # Calculer le nombre de jours dans l'année (gérer les années bissextiles)
    days_in_year = 366 if isleap(year) else 365
    total_hours = days_in_year * 24
    
    equipment_availability = []
    all_equipments = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.is_active == True
    ).all()
    
    for equipment in all_equipments:
        # Récupérer tous les incidents pour cet équipement dans l'année sélectionnée
        equipment_incidents = db.query(Incident).filter(
            and_(
                Incident.service_instance_id == equipment.id,
                Incident.copro_id == copro.id,
                Incident.created_at >= start_date,
                Incident.created_at <= end_date
            )
        ).all()
        
        incident_count = len(equipment_incidents)
        
        # Calculer le temps total en panne
        downtime_hours = 0
        total_resolution_time = 0
        resolved_count = 0
        
        for incident in equipment_incidents:
            if incident.resolved_at and incident.created_at:
                # Incident résolu : temps de résolution (limité à la période de l'année)
                incident_start = max(incident.created_at, start_date)
                incident_end = min(incident.resolved_at, end_date)
                resolution_time = (incident_end - incident_start).total_seconds() / 3600
                downtime_hours += resolution_time
                total_resolution_time += resolution_time
                resolved_count += 1
            elif incident.created_at:
                # Incident non résolu : temps depuis la création jusqu'à la fin de l'année (ou maintenant si année en cours)
                incident_start = max(incident.created_at, start_date)
                incident_end = min(datetime.utcnow(), end_date)
                downtime_hours += (incident_end - incident_start).total_seconds() / 3600
        
        # Calculer la disponibilité
        availability_percent = ((total_hours - downtime_hours) / total_hours * 100) if total_hours > 0 else 100.0
        availability_percent = max(0.0, min(100.0, availability_percent))  # Clamp entre 0 et 100
        
        # Temps moyen de résolution (seulement pour les incidents résolus)
        avg_resolution_hours = (total_resolution_time / resolved_count) if resolved_count > 0 else None
        
        equipment_availability.append({
            "equipment_id": equipment.id,
            "equipment_name": equipment.name,
            "availability_percent": round(availability_percent, 2),
            "incident_count": incident_count,
            "avg_resolution_hours": round(avg_resolution_hours, 2) if avg_resolution_hours else None
        })
    
    return {
        "year": year,
        "incidents_by_day": incidents_by_day,
        "all_incidents": all_incidents,
        "resolution_time_by_equipment": resolution_time_by_equipment,
        "equipment_availability": equipment_availability
    }


@router.get("/statistics/by-building/{building_id}", response_model=dict)
async def get_public_statistics_by_building(
    building_id: int,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Obtenir les statistiques des incidents par bâtiment (public, sans authentification)
    
    Args:
        building_id: ID du bâtiment
        year: Année pour laquelle calculer les statistiques (par défaut: année en cours)
    """
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return {
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": [],
            "equipment_availability": []
        }
    
    # Vérifier que le bâtiment existe et appartient à la copropriété
    building = db.query(Building).filter(
        Building.id == building_id,
        Building.copro_id == copro.id
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Si aucune année n'est spécifiée, utiliser l'année en cours
    if year is None:
        year = datetime.utcnow().year
    
    # Dates de début et fin de l'année (1er janvier 00:00:00 au 31 décembre 23:59:59)
    start_date = datetime(year, 1, 1, 0, 0, 0)
    end_date = datetime(year, 12, 31, 23, 59, 59)
    
    # Récupérer les IDs des équipements du bâtiment
    equipment_ids = [si.id for si in db.query(ServiceInstance.id).filter(
        ServiceInstance.building_id == building_id,
        ServiceInstance.copro_id == copro.id
    ).all()]
    
    if not equipment_ids:
        return {
            "building_id": building_id,
            "building_name": building.name,
            "year": year,
            "incidents_by_day": [],
            "all_incidents": [],
            "resolution_time_by_equipment": [],
            "equipment_availability": []
        }
    
    # Nombre d'incidents par jour sur l'année sélectionnée pour ce bâtiment
    incidents_by_day_query = db.query(
        sql_func.date(Incident.created_at).label('date'),
        sql_func.count(Incident.id).label('count')
    ).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.created_at >= start_date,
            Incident.created_at <= end_date,
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
    
    # Tous les incidents pour ce bâtiment dans l'année sélectionnée
    all_incidents_query = db.query(Incident).filter(
        and_(
            Incident.copro_id == copro.id,
            Incident.service_instance_id.in_(equipment_ids),
            Incident.created_at >= start_date,
            Incident.created_at <= end_date
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
    
    # Calcul de la disponibilité par équipement pour ce bâtiment
    # Période de référence : année complète
    # Calculer le nombre de jours dans l'année (gérer les années bissextiles)
    from calendar import isleap
    days_in_year = 366 if isleap(year) else 365
    total_hours = days_in_year * 24
    
    equipment_availability = []
    building_equipments = db.query(ServiceInstance).filter(
        ServiceInstance.building_id == building_id,
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.is_active == True
    ).all()
    
    for equipment in building_equipments:
        # Récupérer tous les incidents pour cet équipement dans l'année sélectionnée
        equipment_incidents = db.query(Incident).filter(
            and_(
                Incident.service_instance_id == equipment.id,
                Incident.copro_id == copro.id,
                Incident.created_at >= start_date,
                Incident.created_at <= end_date
            )
        ).all()
        
        incident_count = len(equipment_incidents)
        
        # Calculer le temps total en panne
        downtime_hours = 0
        total_resolution_time = 0
        resolved_count = 0
        
        for incident in equipment_incidents:
            if incident.resolved_at and incident.created_at:
                # Incident résolu : temps de résolution (limité à la période de l'année)
                incident_start = max(incident.created_at, start_date)
                incident_end = min(incident.resolved_at, end_date)
                resolution_time = (incident_end - incident_start).total_seconds() / 3600
                downtime_hours += resolution_time
                total_resolution_time += resolution_time
                resolved_count += 1
            elif incident.created_at:
                # Incident non résolu : temps depuis la création jusqu'à la fin de l'année (ou maintenant si année en cours)
                incident_start = max(incident.created_at, start_date)
                incident_end = min(datetime.utcnow(), end_date)
                downtime_hours += (incident_end - incident_start).total_seconds() / 3600
        
        # Calculer la disponibilité
        availability_percent = ((total_hours - downtime_hours) / total_hours * 100) if total_hours > 0 else 100.0
        availability_percent = max(0.0, min(100.0, availability_percent))  # Clamp entre 0 et 100
        
        # Temps moyen de résolution (seulement pour les incidents résolus)
        avg_resolution_hours = (total_resolution_time / resolved_count) if resolved_count > 0 else None
        
        equipment_availability.append({
            "equipment_id": equipment.id,
            "equipment_name": equipment.name,
            "availability_percent": round(availability_percent, 2),
            "incident_count": incident_count,
            "avg_resolution_hours": round(avg_resolution_hours, 2) if avg_resolution_hours else None
        })
    
    return {
        "building_id": building_id,
        "building_name": building.name,
        "year": year,
        "incidents_by_day": incidents_by_day,
        "all_incidents": all_incidents,
        "resolution_time_by_equipment": resolution_time_by_equipment,
        "equipment_availability": equipment_availability
    }

