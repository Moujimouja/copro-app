from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.db import get_db
from app.models.status import Service, Incident, IncidentUpdate, ServiceStatus, IncidentStatus
from app.models.copro import ServiceInstance, Copro
from app.models.maintenance import Maintenance
from pydantic import BaseModel

router = APIRouter()


# Pydantic schemas
class ServiceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    order: int
    building_id: Optional[int] = None
    building_name: Optional[str] = None

    class Config:
        from_attributes = True
        
    @classmethod
    def from_service(cls, service: Service):
        """Convert Service model to response"""
        return cls(
            id=service.id,
            name=service.name,
            description=service.description,
            status=service.status.value,
            order=service.order
        )


class IncidentUpdateResponse(BaseModel):
    id: int
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_update(cls, update: IncidentUpdate):
        """Convert IncidentUpdate model to response"""
        return cls(
            id=update.id,
            message=update.message,
            status=update.status.value,
            created_at=update.created_at
        )


class IncidentResponse(BaseModel):
    id: int
    service_id: Optional[int]
    service_instance_id: Optional[int] = None
    title: str
    message: Optional[str]
    status: str
    is_scheduled: bool
    scheduled_for: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime]
    updates: List[IncidentUpdateResponse] = []
    equipment_status: Optional[str] = None  # Statut de l'équipement concerné

    class Config:
        from_attributes = True
        
    @classmethod
    def from_incident(cls, incident: Incident):
        """Convert Incident model to response"""
        # Récupérer le statut de l'équipement si un équipement est associé
        equipment_status = None
        if incident.service_instance_id and incident.service_instance:
            equipment_status = incident.service_instance.status
        
        return cls(
            id=incident.id,
            service_id=incident.service_id,
            service_instance_id=incident.service_instance_id,
            title=incident.title,
            message=incident.message,
            status=incident.status.value,
            is_scheduled=incident.is_scheduled,
            scheduled_for=incident.scheduled_for,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at,
            updates=[IncidentUpdateResponse.from_update(update) for update in incident.updates] if incident.updates else [],
            equipment_status=equipment_status
        )


class CoproInfo(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    class Config:
        from_attributes = True


class MaintenanceTimelineResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: datetime
    service_instance_ids: List[int]
    type: str = "maintenance"  # Pour distinguer des incidents dans la timeline

    class Config:
        from_attributes = True


class StatusPageResponse(BaseModel):
    services: List[ServiceResponse]
    incidents: List[IncidentResponse]
    maintenances: List[MaintenanceTimelineResponse] = []  # Maintenances actives
    overall_status: str  # Overall system status
    copro: Optional[CoproInfo] = None


@router.get("/services", response_model=List[ServiceResponse])
async def get_services(db: Session = Depends(get_db)):
    """Get all active services"""
    services = db.query(Service).filter(Service.is_active == True).order_by(Service.order, Service.name).all()
    return [ServiceResponse.from_service(s) for s in services]


@router.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent incidents (public endpoint)"""
    incidents = db.query(Incident).order_by(desc(Incident.created_at)).limit(limit).all()
    return [IncidentResponse.from_incident(i) for i in incidents]


@router.get("/status", response_model=StatusPageResponse)
async def get_status_page(db: Session = Depends(get_db)):
    """Get complete status page data (public endpoint) - Une seule copropriété"""
    # Récupérer la première (et seule) copropriété
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        return {
            "services": [],
            "incidents": [],
            "maintenances": [],
            "overall_status": "operational",
            "copro": None
        }
    
    # Utiliser ServiceInstance au lieu de Service (ancien modèle)
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.is_active == True
    ).order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    # Get recent incidents (last 20) avec les relations chargées
    from sqlalchemy.orm import joinedload
    incidents = db.query(Incident).options(
        joinedload(Incident.service_instance)
    ).filter(
        Incident.copro_id == copro.id
    ).order_by(desc(Incident.created_at)).limit(20).all()
    
    # Get active maintenances (maintenances dont la date actuelle est entre start_date et end_date)
    now = datetime.utcnow()
    active_maintenances = db.query(Maintenance).filter(
        Maintenance.copro_id == copro.id,
        Maintenance.start_date <= now,
        Maintenance.end_date >= now
    ).all()
    
    # Créer un set des IDs d'équipements en maintenance
    equipment_ids_in_maintenance = set()
    maintenances_data = []
    for maintenance in active_maintenances:
        db.refresh(maintenance, ['service_instances'])
        service_instance_ids = [si.id for si in maintenance.service_instances]
        equipment_ids_in_maintenance.update(service_instance_ids)
        maintenances_data.append(MaintenanceTimelineResponse(
            id=maintenance.id,
            title=maintenance.title,
            description=maintenance.description,
            start_date=maintenance.start_date,
            end_date=maintenance.end_date,
            service_instance_ids=service_instance_ids
        ))
    
    # Calculate overall status (prendre en compte les maintenances actives)
    if not service_instances:
        overall_status = "operational"
    else:
        # Construire la liste des statuts en incluant "maintenance" pour les équipements en maintenance active
        statuses = []
        for si in service_instances:
            if si.id in equipment_ids_in_maintenance:
                statuses.append("maintenance")
            else:
                statuses.append(si.status)
        
        if "major_outage" in statuses:
            overall_status = "major_outage"
        elif "partial_outage" in statuses:
            overall_status = "partial_outage"
        elif "degraded" in statuses:
            overall_status = "degraded"
        elif "maintenance" in statuses:
            overall_status = "maintenance"
        else:
            overall_status = "operational"
    
    # Convertir ServiceInstance en ServiceResponse
    services_data = []
    for si in service_instances:
        db.refresh(si, ['building'])
        
        # Nettoyer le nom pour enlever l'identifier entre parenthèses (ex: "Ascenseur 1 (ASC-A-01)" -> "Ascenseur 1")
        display_name = si.name
        if '(' in si.name and ')' in si.name:
            # Extraire la partie avant les parenthèses
            display_name = si.name.split('(')[0].strip()
        
        # Si l'équipement est en maintenance active, forcer le statut à "maintenance"
        equipment_status = si.status
        if si.id in equipment_ids_in_maintenance:
            equipment_status = "maintenance"
        
        services_data.append(ServiceResponse(
            id=si.id,
            name=display_name,
            description=si.description,
            status=equipment_status,
            order=si.order,
            building_id=si.building_id,
            building_name=si.building.name if si.building else None
        ))
    
    return {
        "services": services_data,
        "incidents": [IncidentResponse.from_incident(i) for i in incidents],
        "maintenances": maintenances_data,
        "overall_status": overall_status,
        "copro": CoproInfo(
            id=copro.id,
            name=copro.name,
            address=copro.address,
            city=copro.city,
            postal_code=copro.postal_code,
            country=copro.country
        ) if copro else None
    }


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get a specific incident with all updates"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.from_incident(incident)

