"""
Modèles pour la gestion multi-tenant des copropriétés
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Copro(Base):
    """Copropriété - Entité principale multi-tenant"""
    __tablename__ = "copros"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Nom de la copropriété
    address = Column(Text, nullable=True)  # Adresse complète
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, default="France", nullable=False)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    buildings = relationship("Building", back_populates="copro", cascade="all, delete-orphan")
    users = relationship("User", back_populates="copro")
    service_types = relationship("ServiceType", back_populates="copro", cascade="all, delete-orphan")


class Building(Base):
    """Bâtiment dans une copropriété"""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # Nom unique du bâtiment (ex: "Bâtiment A", "Bâtiment B")
    description = Column(Text, nullable=True)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # Pour l'ordre d'affichage
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    copro = relationship("Copro", back_populates="buildings")
    service_instances = relationship("ServiceInstance", back_populates="building", cascade="all, delete-orphan")

    # Unique constraint: un nom unique par copropriété
    __table_args__ = (
        Index('ix_buildings_copro_name', 'copro_id', 'name', unique=True),
    )


class ServiceType(Base):
    """Type de service/équipement (template réutilisable)"""
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # "Ascenseur", "Éclairage", "Eau chaude", etc.
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Nom d'icône ou emoji
    category = Column(String, nullable=True)  # "Équipement", "Fluide", "Sécurité", etc.
    
    # Configuration par défaut
    default_status = Column(String, default="operational")  # Status par défaut
    
    # Métadonnées
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    copro = relationship("Copro", back_populates="service_types")
    service_instances = relationship("ServiceInstance", back_populates="service_type", cascade="all, delete-orphan")


class ServiceInstance(Base):
    """Instance réelle d'un service dans un bâtiment"""
    __tablename__ = "service_instances"

    id = Column(Integer, primary_key=True, index=True)
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=False, index=True)
    
    # Identification
    name = Column(String, nullable=False)  # Nom spécifique (ex: "Ascenseur Bâtiment A")
    identifier = Column(String, nullable=True)  # Identifiant optionnel (ex: "ASC-A-01")
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)  # Localisation précise (ex: "Rez-de-chaussée")
    
    # Status (référence au modèle status.ServiceStatus)
    status = Column(String, default="operational", nullable=False)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    building = relationship("Building", back_populates="service_instances")
    service_type = relationship("ServiceType", back_populates="service_instances")
    incidents = relationship("Incident", back_populates="service_instance", cascade="all, delete-orphan")

    # Unique constraint: nom unique par copropriété
    __table_args__ = (
        Index('ix_service_instances_copro_name', 'copro_id', 'name', unique=True),
    )


