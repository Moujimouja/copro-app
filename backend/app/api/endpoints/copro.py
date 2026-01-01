"""
API endpoints pour la gestion des copropriétés, bâtiments et services
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db import get_db
from app.models.copro import Copro, Building, ServiceInstance
from app.models.status import ServiceStatus

router = APIRouter()


# ============ Pydantic Schemas ============

class CoproBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "France"


class CoproCreate(CoproBase):
    pass


class CoproResponse(CoproBase):
    id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class BuildingBase(BaseModel):
    name: str  # Nom unique du bâtiment
    description: Optional[str] = None
    order: int = 0


class BuildingCreate(BuildingBase):
    copro_id: int


class BuildingResponse(BuildingBase):
    id: int
    copro_id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ServiceInstanceBase(BaseModel):
    building_id: int
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: str = "operational"
    order: int = 0


class ServiceInstanceCreate(ServiceInstanceBase):
    copro_id: int


class ServiceInstanceResponse(ServiceInstanceBase):
    id: int
    copro_id: int
    is_active: bool
    building: BuildingResponse
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# ============ Copro Endpoints ============

@router.post("/copros", response_model=CoproResponse, status_code=status.HTTP_201_CREATED)
async def create_copro(copro: CoproCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle copropriété"""
    db_copro = Copro(**copro.dict())
    db.add(db_copro)
    db.commit()
    db.refresh(db_copro)
    return db_copro


@router.get("/copros", response_model=List[CoproResponse])
async def list_copros(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lister toutes les copropriétés"""
    copros = db.query(Copro).filter(Copro.is_active == True).offset(skip).limit(limit).all()
    return copros


@router.get("/copros/{copro_id}", response_model=CoproResponse)
async def get_copro(copro_id: int, db: Session = Depends(get_db)):
    """Obtenir une copropriété par ID"""
    copro = db.query(Copro).filter(Copro.id == copro_id).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Copropriété non trouvée")
    return copro


# ============ Building Endpoints ============

@router.post("/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(building: BuildingCreate, db: Session = Depends(get_db)):
    """Créer un nouveau bâtiment"""
    # Vérifier que la copropriété existe
    copro = db.query(Copro).filter(Copro.id == building.copro_id).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Copropriété non trouvée")
    
    # Vérifier l'unicité du nom dans la copropriété
    existing = db.query(Building).filter(
        Building.copro_id == building.copro_id,
        Building.name == building.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un bâtiment avec le nom '{building.name}' existe déjà")
    
    db_building = Building(**building.dict())
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building


@router.get("/copros/{copro_id}/buildings", response_model=List[BuildingResponse])
async def list_buildings(copro_id: int, db: Session = Depends(get_db)):
    """Lister les bâtiments d'une copropriété"""
    buildings = db.query(Building).filter(
        Building.copro_id == copro_id,
        Building.is_active == True
    ).order_by(Building.order, Building.name).all()
    return buildings


# ============ ServiceInstance Endpoints ============

@router.post("/service-instances", response_model=ServiceInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_service_instance(service_instance: ServiceInstanceCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle instance de service"""
    # Vérifier que la copropriété existe
    copro = db.query(Copro).filter(Copro.id == service_instance.copro_id).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Copropriété non trouvée")
    
    # Vérifier que le bâtiment existe et appartient à la copropriété
    building = db.query(Building).filter(
        Building.id == service_instance.building_id,
        Building.copro_id == service_instance.copro_id
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Vérifier l'unicité du nom dans la copropriété
    existing = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == service_instance.copro_id,
        ServiceInstance.name == service_instance.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Un service avec le nom '{service_instance.name}' existe déjà")
    
    db_service_instance = ServiceInstance(**service_instance.dict())
    db.add(db_service_instance)
    db.commit()
    db.refresh(db_service_instance)
    
    # Charger les relations pour la réponse
    db.refresh(db_service_instance, ['building'])
    return db_service_instance


@router.get("/copros/{copro_id}/service-instances", response_model=List[ServiceInstanceResponse])
async def list_service_instances(copro_id: int, building_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Lister les instances de services d'une copropriété (optionnellement filtrées par bâtiment)"""
    query = db.query(ServiceInstance).filter(
        ServiceInstance.copro_id == copro_id,
        ServiceInstance.is_active == True
    )
    
    if building_id:
        query = query.filter(ServiceInstance.building_id == building_id)
    
    service_instances = query.order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    # Charger les relations
    for instance in service_instances:
        db.refresh(instance, ['building'])
    
    return service_instances


@router.get("/buildings/{building_id}/service-instances", response_model=List[ServiceInstanceResponse])
async def list_building_service_instances(building_id: int, db: Session = Depends(get_db)):
    """Lister les services d'un bâtiment spécifique"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    service_instances = db.query(ServiceInstance).filter(
        ServiceInstance.building_id == building_id,
        ServiceInstance.is_active == True
    ).order_by(ServiceInstance.order, ServiceInstance.name).all()
    
    for instance in service_instances:
        db.refresh(instance, ['building'])
    
    return service_instances


