from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)  # Optionnel, on utilise email pour la connexion
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Informations personnelles
    first_name = Column(String, nullable=True)  # Prénom (obligatoire pour nouveaux utilisateurs)
    last_name = Column(String, nullable=True)  # Nom (obligatoire pour nouveaux utilisateurs)
    lot_number = Column(String, nullable=True)  # Numéro de lot (optionnel)
    floor = Column(String, nullable=True)  # Étage (optionnel)
    
    # Multi-tenant: association à une copropriété
    copro_id = Column(Integer, ForeignKey("copros.id"), nullable=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True, index=True)  # Bâtiment (obligatoire pour nouveaux utilisateurs)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    copro = relationship("Copro", back_populates="users")
    building = relationship("Building")

