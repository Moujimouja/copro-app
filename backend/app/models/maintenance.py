"""
Modèle pour la gestion des maintenances planifiées
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

# Table de liaison many-to-many entre Maintenance et ServiceInstance
maintenance_service_instances = Table(
    'maintenance_service_instances',
    Base.metadata,
    Column('maintenance_id', Integer, ForeignKey('maintenances.id', ondelete='CASCADE'), primary_key=True),
    Column('service_instance_id', Integer, ForeignKey('service_instances.id', ondelete='CASCADE'), primary_key=True)
)


class Maintenance(Base):
    """Maintenance planifiée pour un ou plusieurs équipements"""
    __tablename__ = "maintenances"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=False, index=True)
    title = Column(String, nullable=False)  # Titre de la maintenance
    description = Column(Text, nullable=True)  # Description optionnelle
    start_date = Column(DateTime(timezone=True), nullable=False)  # Date/heure de début
    end_date = Column(DateTime(timezone=True), nullable=False)  # Date/heure de fin
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    copro = relationship("Copro", back_populates="maintenances")
    service_instances = relationship(
        "ServiceInstance",
        secondary=maintenance_service_instances,
        back_populates="maintenances"
    )


