from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.db import Base


class ServiceStatus(PyEnum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"
    MAINTENANCE = "maintenance"


class IncidentStatus(PyEnum):
    INVESTIGATING = "investigating"  # En cours d'analyse
    IN_PROGRESS = "in_progress"  # En cours de traitement
    RESOLVED = "resolved"  # Résolu
    CLOSED = "closed"  # Clos (visible dans les incidents passés)
    SCHEDULED = "scheduled"  # Planifié


class Service(Base):
    """Service/Component that can have status (elevator, door, heating, etc.)
    DEPRECATED: Utiliser ServiceInstance à la place pour le multi-tenant
    Conservé pour compatibilité ascendante
    """
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ServiceStatus), default=ServiceStatus.OPERATIONAL, nullable=False)
    order = Column(Integer, default=0)  # For ordering display
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    incidents = relationship("Incident", back_populates="service", cascade="all, delete-orphan")


class Incident(Base):
    """Incident/Event affecting a service"""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=True, index=True)  # Multi-tenant
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # DEPRECATED: utiliser service_instance_id
    service_instance_id = Column(Integer, ForeignKey("service_instances.id"), nullable=True, index=True)  # Nouveau
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.INVESTIGATING, nullable=False)
    is_scheduled = Column(Boolean, default=False)  # Scheduled maintenance
    scheduled_for = Column(DateTime(timezone=True), nullable=True)  # When scheduled maintenance starts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    service = relationship("Service", back_populates="incidents")  # DEPRECATED
    service_instance = relationship("ServiceInstance", back_populates="incidents")
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentUpdate.created_at")
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentComment.created_at")


class IncidentUpdate(Base):
    """Updates/updates for an incident"""
    __tablename__ = "incident_updates"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(IncidentStatus), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    incident = relationship("Incident", back_populates="updates")


class IncidentComment(Base):
    """Commentaires des administrateurs sur un incident"""
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    incident = relationship("Incident", back_populates="comments")
    admin = relationship("User")

