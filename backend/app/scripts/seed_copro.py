"""
Script de seed pour créer facilement une copropriété avec ses bâtiments et services
Usage: python -m app.scripts.seed_copro
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal, engine, Base
from app.models.copro import Copro, Building, ServiceType, ServiceInstance
from app.models.status import ServiceStatus


def create_sample_copro():
    """Créer une copropriété d'exemple avec bâtiments et services"""
    db = SessionLocal()
    
    try:
        # 1. Créer la copropriété
        copro = Copro(
            name="Résidence Les Jardins",
            address="123 Avenue de la République",
            city="Paris",
            postal_code="75011",
            country="France"
        )
        db.add(copro)
        db.commit()
        db.refresh(copro)
        print(f"✅ Copropriété créée: {copro.name} (ID: {copro.id})")
        
        # 2. Créer les bâtiments
        buildings_data = [
            {"identifier": "A", "name": "Bâtiment A", "order": 1},
            {"identifier": "B", "name": "Bâtiment B", "order": 2},
            {"identifier": "C", "name": "Bâtiment C", "order": 3},
        ]
        
        buildings = []
        for b_data in buildings_data:
            building = Building(
                copro_id=copro.id,
                **b_data
            )
            db.add(building)
            buildings.append(building)
        
        db.commit()
        for building in buildings:
            db.refresh(building)
            print(f"✅ Bâtiment créé: {building.identifier} - {building.name} (ID: {building.id})")
        
        # 3. Créer les types de services
        service_types_data = [
            {
                "name": "Ascenseur",
                "description": "Ascenseur de l'immeuble",
                "icon": "🚁",
                "category": "Équipement",
                "default_status": "operational",
                "order": 1
            },
            {
                "name": "Éclairage",
                "description": "Éclairage des parties communes",
                "icon": "💡",
                "category": "Équipement",
                "default_status": "operational",
                "order": 2
            },
            {
                "name": "Eau chaude",
                "description": "Production d'eau chaude sanitaire",
                "icon": "🔥",
                "category": "Fluide",
                "default_status": "operational",
                "order": 3
            },
            {
                "name": "Eau froide",
                "description": "Distribution d'eau froide",
                "icon": "💧",
                "category": "Fluide",
                "default_status": "operational",
                "order": 4
            },
            {
                "name": "Porte parking",
                "description": "Porte d'accès au parking",
                "icon": "🚗",
                "category": "Sécurité",
                "default_status": "operational",
                "order": 5
            },
            {
                "name": "Chauffage",
                "description": "Système de chauffage central",
                "icon": "🌡️",
                "category": "Fluide",
                "default_status": "operational",
                "order": 6
            },
        ]
        
        service_types = []
        for st_data in service_types_data:
            service_type = ServiceType(
                copro_id=copro.id,
                **st_data
            )
            db.add(service_type)
            service_types.append(service_type)
        
        db.commit()
        for service_type in service_types:
            db.refresh(service_type)
            print(f"✅ Type de service créé: {service_type.name} (ID: {service_type.id})")
        
        # 4. Créer les instances de services pour chaque bâtiment
        service_instances = []
        
        for building in buildings:
            for service_type in service_types:
                # Nom du service: "Type - Bâtiment X"
                service_name = f"{service_type.name} - Bâtiment {building.identifier}"
                identifier = f"{service_type.name[:3].upper()}-{building.identifier}"
                
                service_instance = ServiceInstance(
                    copro_id=copro.id,
                    building_id=building.id,
                    service_type_id=service_type.id,
                    name=service_name,
                    identifier=identifier,
                    description=f"{service_type.description} du bâtiment {building.identifier}",
                    location=f"Bâtiment {building.identifier}",
                    status=service_type.default_status,
                    order=service_type.order
                )
                db.add(service_instance)
                service_instances.append(service_instance)
        
        db.commit()
        print(f"✅ {len(service_instances)} instances de services créées")
        
        # Résumé
        print("\n" + "="*50)
        print("RÉSUMÉ DE LA COPRIOPRIÉTÉ CRÉÉE")
        print("="*50)
        print(f"Copropriété: {copro.name}")
        print(f"Bâtiments: {len(buildings)}")
        print(f"Types de services: {len(service_types)}")
        print(f"Instances de services: {len(service_instances)}")
        print("="*50)
        
        return copro
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def create_custom_copro(name: str, buildings: list, service_types: list):
    """
    Créer une copropriété personnalisée
    
    Args:
        name: Nom de la copropriété
        buildings: Liste d'identifiants de bâtiments (ex: ["A", "B", "1", "2"])
        service_types: Liste de dictionnaires avec les types de services
            Ex: [{"name": "Ascenseur", "icon": "🚁", "category": "Équipement"}, ...]
    """
    db = SessionLocal()
    
    try:
        # Créer la copropriété
        copro = Copro(name=name)
        db.add(copro)
        db.commit()
        db.refresh(copro)
        
        # Créer les bâtiments
        db_buildings = []
        for idx, building_id in enumerate(buildings):
            building = Building(
                copro_id=copro.id,
                identifier=building_id,
                name=f"Bâtiment {building_id}",
                order=idx + 1
            )
            db.add(building)
            db_buildings.append(building)
        
        db.commit()
        for building in db_buildings:
            db.refresh(building)
        
        # Créer les types de services
        db_service_types = []
        for idx, st_data in enumerate(service_types):
            service_type = ServiceType(
                copro_id=copro.id,
                name=st_data.get("name"),
                description=st_data.get("description"),
                icon=st_data.get("icon"),
                category=st_data.get("category", "Équipement"),
                default_status=st_data.get("default_status", "operational"),
                order=idx + 1
            )
            db.add(service_type)
            db_service_types.append(service_type)
        
        db.commit()
        for service_type in db_service_types:
            db.refresh(service_type)
        
        # Créer les instances pour chaque combinaison bâtiment/service
        for building in db_buildings:
            for service_type in db_service_types:
                service_instance = ServiceInstance(
                    copro_id=copro.id,
                    building_id=building.id,
                    service_type_id=service_type.id,
                    name=f"{service_type.name} - Bâtiment {building.identifier}",
                    identifier=f"{service_type.name[:3].upper()}-{building.identifier}",
                    status=service_type.default_status
                )
                db.add(service_instance)
        
        db.commit()
        print(f"✅ Copropriété '{name}' créée avec succès!")
        return copro
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    # Créer une copropriété d'exemple
    create_sample_copro()


