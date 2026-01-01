from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.db import get_db
from app.models.user import User
from app.models.copro import Copro, Building
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from app.core.config import settings

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str  # Obligatoire
    last_name: str  # Obligatoire
    building_id: int  # Obligatoire
    lot_number: Optional[str] = None  # Optionnel
    floor: Optional[str] = None  # Optionnel

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        return v


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Enregistrer un nouvel utilisateur (public) - Compte inactif par défaut"""
    # Vérifier que l'email n'existe pas déjà
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email existe déjà"
        )
    
    # Vérifier que le bâtiment existe
    building = db.query(Building).filter(Building.id == user_data.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Bâtiment non trouvé")
    
    # Récupérer la copropriété active
    copro = db.query(Copro).filter(Copro.is_active == True).first()
    if not copro:
        raise HTTPException(status_code=404, detail="Aucune copropriété configurée")
    
    # Créer le nouvel utilisateur (inactif par défaut)
    # Générer un username basé sur l'email pour la compatibilité (partie avant @)
    username_from_email = user_data.email.split('@')[0]
    # S'assurer que le username est unique
    base_username = username_from_email
    counter = 1
    while db.query(User).filter(User.username == username_from_email).first():
        username_from_email = f"{base_username}{counter}"
        counter += 1
    
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=username_from_email,  # Généré automatiquement depuis l'email
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        lot_number=user_data.lot_number,
        floor=user_data.floor,
        building_id=user_data.building_id,
        copro_id=copro.id,
        is_active=False,  # Compte inactif par défaut
        is_superuser=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token - Utilise email au lieu de username"""
    # OAuth2PasswordRequestForm utilise 'username' comme nom de champ, mais on l'utilise pour l'email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte inactif. Veuillez contacter un administrateur."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "is_superuser": user.is_superuser}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


