from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import engine, Base, SessionLocal
from app.api import api_router
# Import models to ensure tables are created
from app.models import User, Service, Incident, IncidentUpdate, IncidentComment, Copro, Building, ServiceInstance, Ticket, Maintenance
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize test data if requested
if os.getenv("INIT_TEST_DATA", "false").lower() == "true":
    try:
        from app.scripts.init_test_data import init_test_data
        print("🔄 Initialisation des données de test...")
        init_test_data()
        print("✅ Données de test initialisées")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation des données de test: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://127.0.0.1:5173"],  # Include settings + localhost variants
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Copro App API", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

