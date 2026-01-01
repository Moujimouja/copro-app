"""
Script de seed pour créer facilement une copropriété avec ses bâtiments et services
Usage: python -m app.scripts.seed_copro
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal, engine, Base
from app.models.copro import Copro, Building, ServiceInstance
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
            {"name": "Bâtiment A", "order": 1},
            {"name": "Bâtiment B", "order": 2},
            {"name": "Bâtiment C", "order": 3},
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
            print(f"✅ Bâtiment créé: {building.name} (ID: {building.id})")
        
        # 3. Créer les équipements pour chaque bâtiment
        equipment_names = ["Ascenseur", "Éclairage", "Eau chaude", "Eau froide", "Porte parking", "Chauffage"]
        service_instances = []
        order_counter = 1
        
        for building in buildings:
            for eq_name in equipment_names:
                building_short = building.name.replace("Bâtiment ", "").replace(" ", "")
                service_name = f"{eq_name} - {building.name}"
                identifier = f"{eq_name[:3].upper()}-{building_short}"
                
                service_instance = ServiceInstance(
                    copro_id=copro.id,
                    building_id=building.id,
                    name=service_name,
                    identifier=identifier,
                    description=f"{eq_name}",
                    location=None,
                    status="operational",
                    order=order_counter
                )
                db.add(service_instance)
                service_instances.append(service_instance)
                order_counter += 1
        
        db.commit()
        print(f"✅ {len(service_instances)} équipements créés")
        
        # Résumé
        print("\n" + "="*50)
        print("RÉSUMÉ DE LA COPRIOPRIÉTÉ CRÉÉE")
        print("="*50)
        print(f"Copropriété: {copro.name}")
        print(f"Bâtiments: {len(buildings)}")
        print(f"Équipements: {len(service_instances)}")
        print("="*50)
        
        return copro
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


def create_custom_copro(name: str, buildings: list, equipment_names: list):
    """
    Créer une copropriété personnalisée
    
    Args:
        name: Nom de la copropriété
        buildings: Liste d'identifiants de bâtiments (ex: ["A", "B", "1", "2"])
        equipment_names: Liste de noms d'équipements (ex: ["Ascenseur", "Éclairage", ...])
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
        for idx, building_name in enumerate(buildings):
            building = Building(
                copro_id=copro.id,
                name=building_name if building_name.startswith("Bâtiment") else f"Bâtiment {building_name}",
                order=idx + 1
            )
            db.add(building)
            db_buildings.append(building)
        
        db.commit()
        for building in db_buildings:
            db.refresh(building)
        
        # Créer les équipements pour chaque combinaison bâtiment/équipement
        order_counter = 1
        for building in db_buildings:
            for eq_name in equipment_names:
                building_short = building.name.replace("Bâtiment ", "").replace(" ", "")
                service_instance = ServiceInstance(
                    copro_id=copro.id,
                    building_id=building.id,
                    name=f"{eq_name} - {building.name}",
                    identifier=f"{eq_name[:3].upper()}-{building_short}",
                    status="operational",
                    order=order_counter
                )
                db.add(service_instance)
                order_counter += 1
        
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


