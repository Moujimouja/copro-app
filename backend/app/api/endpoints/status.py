from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.db import get_db
from app.models.status import Service, Incident, IncidentUpdate, ServiceStatus, IncidentStatus
from app.models.copro import ServiceInstance, Copro
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
    building_identifier: Optional[str] = None
    building_name: Optional[str] = None
    service_type_id: Optional[int] = None
    service_type_name: Optional[str] = None

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
    title: str
    message: Optional[str]
    status: str
    is_scheduled: bool
    scheduled_for: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    updates: List[IncidentUpdateResponse] = []

    class Config:
        from_attributes = True
        
    @classmethod
    def from_incident(cls, incident: Incident):
        """Convert Incident model to response"""
        return cls(
            id=incident.id,
            service_id=incident.service_id,
            title=incident.title,
            message=incident.message,
            status=incident.status.value,
            is_scheduled=incident.is_scheduled,
            scheduled_for=incident.scheduled_for,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at,
            updates=[IncidentUpdateResponse.from_update(update) for update in incident.updates] if incident.updates else []
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


class StatusPageResponse(BaseModel):
    services: List[ServiceResponse]
    incidents: List[IncidentResponse]
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
            "overall_status": "operational",
            "copro": None
        }
    
    # Utiliser ServiceInstance au lieu de Service (ancien modèle)
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro.id,
        ServiceInstance.is_active == True
    ).order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    # Get recent incidents (last 20)
    incidents = db.query(Incident).filter(
        Incident.copro_id == copro.id
    ).order_by(desc(Incident.created_at)).limit(20).all()
    
    # Calculate overall status
    if not service_instances:
        overall_status = "operational"
    else:
        statuses = [si.status for si in service_instances]
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
        db.refresh(si, ['building', 'service_type'])
        services_data.append(ServiceResponse(
            id=si.id,
            name=si.name,
            description=si.description or f"{si.service_type.name if si.service_type else ''} - Bâtiment {si.building.identifier if si.building else ''}",
            status=si.status,
            order=si.order,
            building_id=si.building_id,
            building_identifier=si.building.identifier if si.building else None,
            building_name=si.building.name if si.building else None,
            service_type_id=si.service_type_id,
            service_type_name=si.service_type.name if si.service_type else None
        ))
    
    return {
        "services": services_data,
        "incidents": [IncidentResponse.from_incident(i) for i in incidents],
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

