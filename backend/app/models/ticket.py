"""
Modèle pour les tickets de déclaration d'incidents (public)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from app.db import Base


class TicketStatus(PyEnum):
    ANALYZING = "analyzing"  # En cours d'analyse
    IN_PROGRESS = "in_progress"  # En cours de traitement
    RESOLVED = "resolved"  # Résolu
    CLOSED = "closed"  # Clos


class TicketType(PyEnum):
    INCIDENT = "incident"  # Incident
    REQUEST = "request"  # Demande


class Ticket(Base):
    """Ticket de déclaration d'incident (créé par le public)"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=False, index=True)
    service_instance_id = Column(Integer, ForeignKey("service_instances.id"), nullable=True, index=True)
    
    # Informations du déclarant (public)
    reporter_name = Column(String, nullable=True)  # Nom optionnel
    reporter_email = Column(String, nullable=True)  # Email optionnel
    reporter_phone = Column(String, nullable=True)  # Téléphone optionnel
    
    # Description du problème
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)  # Localisation précise
    
    # Photos/pièces jointes (stockées en JSON ou chemins)
    attachments = Column(Text, nullable=True)  # JSON array de chemins
    
    # Type de ticket
    type = Column(SQLEnum(TicketType), default=TicketType.INCIDENT, nullable=False)
    
    # Statut et gestion
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.ANALYZING, nullable=False)
    admin_notes = Column(Text, nullable=True)  # Notes de l'admin (deprecated, utiliser TicketComment)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Admin assigné
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin qui a traité
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Lien avec incident (si créé)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    copro = relationship("Copro")
    service_instance = relationship("ServiceInstance")
    assigned_admin = relationship("User", foreign_keys=[assigned_to])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    incident = relationship("Incident", foreign_keys=[incident_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")


