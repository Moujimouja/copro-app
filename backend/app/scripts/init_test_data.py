"""
Script d'initialisation des données de test
Crée une copropriété avec 2 bâtiments et tous les équipements nécessaires
Usage: python -m app.scripts.init_test_data
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal, engine, Base
from app.models.copro import Copro, Building, ServiceType, ServiceInstance
from app.models.user import User
import bcrypt


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_admin_if_not_exists(db):
    """Créer un compte admin s'il n'existe pas"""
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        print("ℹ️  Compte admin existe déjà")
        return existing_admin
    
    admin = User(
        username="admin",
        email="admin@copro.local",
        hashed_password=get_password_hash("admin123"),
        is_superuser=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print("✅ Compte admin créé (username: admin, password: admin123)")
    return admin


def init_test_data():
    """Initialiser les données de test"""
    db = SessionLocal()
    
    try:
        # 1. Créer le compte admin si nécessaire
        create_admin_if_not_exists(db)
        
        # 2. Vérifier si une copropriété existe déjà
        existing_copro = db.query(Copro).filter(Copro.is_active == True).first()
        if existing_copro:
            # Vérifier si c'est déjà la copropriété de test
            if existing_copro.name == "Copropriété de Test":
                print("ℹ️  Les données de test existent déjà. Utilisation des données existantes.")
                print(f"   Copropriété: {existing_copro.name} (ID: {existing_copro.id})")
                total_equipments = db.query(ServiceInstance).filter(ServiceInstance.copro_id == existing_copro.id).count()
                print(f"   Équipements: {total_equipments}")
                return
            
            print("⚠️  Une copropriété existe déjà. Suppression des données existantes...")
            # Supprimer les équipements
            db.query(ServiceInstance).filter(ServiceInstance.copro_id == existing_copro.id).delete()
            # Supprimer les types de services
            db.query(ServiceType).filter(ServiceType.copro_id == existing_copro.id).delete()
            # Supprimer les bâtiments
            db.query(Building).filter(Building.copro_id == existing_copro.id).delete()
            # Supprimer la copropriété
            db.delete(existing_copro)
            db.commit()
            print("✅ Données existantes supprimées")
        
        # 3. Créer la copropriété
        copro = Copro(
            name="Copropriété de Test",
            address="123 Rue de la Test",
            city="Paris",
            postal_code="75001",
            country="France",
            is_active=True
        )
        db.add(copro)
        db.flush()
        print(f"✅ Copropriété créée: {copro.name} (ID: {copro.id})")
        
        # 4. Créer les types de services
        service_types_data = [
            {"name": "Ascenseur", "description": "Ascenseur de l'immeuble", "category": "Équipement", "order": 1},
            {"name": "Éclairage", "description": "Éclairage des parties communes", "category": "Équipement", "order": 2},
            {"name": "Eau chaude", "description": "Production d'eau chaude sanitaire", "category": "Fluide", "order": 3},
            {"name": "Eau froide", "description": "Distribution d'eau froide", "category": "Fluide", "order": 4},
            {"name": "Porte parking", "description": "Porte d'accès au parking", "category": "Sécurité", "order": 5},
            {"name": "Électricité", "description": "Alimentation électrique", "category": "Équipement", "order": 6},
            {"name": "Porte d'entrée", "description": "Porte d'entrée du bâtiment", "category": "Sécurité", "order": 7},
            {"name": "Grille voiture", "description": "Grille d'accès voiture", "category": "Sécurité", "order": 8},
            {"name": "Grille piéton", "description": "Grille d'accès piéton", "category": "Sécurité", "order": 9},
        ]
        
        service_types = {}
        for st_data in service_types_data:
            service_type = ServiceType(
                copro_id=copro.id,
                name=st_data["name"],
                description=st_data["description"],
                category=st_data["category"],
                default_status="operational",
                order=st_data["order"],
                is_active=True
            )
            db.add(service_type)
            db.flush()
            service_types[st_data["name"]] = service_type
            print(f"  ✅ Type de service créé: {service_type.name}")
        
        # 5. Créer les 2 bâtiments
        buildings_data = [
            {"identifier": "A", "name": "Bâtiment A", "description": "Premier bâtiment", "order": 1},
            {"identifier": "B", "name": "Bâtiment B", "description": "Deuxième bâtiment", "order": 2},
        ]
        
        buildings = {}
        for b_data in buildings_data:
            building = Building(
                copro_id=copro.id,
                identifier=b_data["identifier"],
                name=b_data["name"],
                description=b_data["description"],
                order=b_data["order"],
                is_active=True
            )
            db.add(building)
            db.flush()
            buildings[b_data["identifier"]] = building
            print(f"✅ Bâtiment créé: {building.identifier} - {building.name} (ID: {building.id})")
        
        # 6. Créer les équipements pour chaque bâtiment
        building_equipments = [
            {"type": "Ascenseur", "count": 2, "prefix": "ASC"},
            {"type": "Eau chaude", "count": 1, "prefix": "EC"},
            {"type": "Eau froide", "count": 1, "prefix": "EF"},
            {"type": "Électricité", "count": 1, "prefix": "ELEC"},
            {"type": "Éclairage", "count": 1, "prefix": "LUM"},
            {"type": "Porte d'entrée", "count": 1, "prefix": "PE"},
        ]
        
        order_counter = 1
        for building_id, building in buildings.items():
            print(f"\n📦 Création des équipements pour le bâtiment {building_id}:")
            for eq_config in building_equipments:
                service_type = service_types[eq_config["type"]]
                for i in range(eq_config["count"]):
                    if eq_config["count"] > 1:
                        name = f"{eq_config['type']} {i+1} - Bâtiment {building_id}"
                        identifier = f"{eq_config['prefix']}-{building_id}-{i+1:02d}"
                    else:
                        name = f"{eq_config['type']} - Bâtiment {building_id}"
                        identifier = f"{eq_config['prefix']}-{building_id}"
                    
                    equipment = ServiceInstance(
                        copro_id=copro.id,
                        building_id=building.id,
                        service_type_id=service_type.id,
                        name=name,
                        identifier=identifier,
                        description=f"{eq_config['type']} du bâtiment {building_id}",
                        status="operational",
                        order=order_counter,
                        is_active=True
                    )
                    db.add(equipment)
                    order_counter += 1
                    print(f"  ✅ {name} ({identifier})")
        
        # 7. Créer un bâtiment "Commun" pour les équipements partagés
        building_common = Building(
            copro_id=copro.id,
            identifier="COMMUN",
            name="Équipements communs",
            description="Équipements partagés entre tous les bâtiments",
            order=99,
            is_active=True
        )
        db.add(building_common)
        db.flush()
        print(f"\n✅ Bâtiment commun créé: {building_common.identifier} - {building_common.name} (ID: {building_common.id})")
        
        # 8. Créer les équipements communs
        print(f"\n📦 Création des équipements communs:")
        common_equipments = [
            {"type": "Porte parking", "identifier": "PP-01", "name": "Porte parking"},
            {"type": "Grille voiture", "identifier": "GV-01", "name": "Grille voiture"},
            {"type": "Grille piéton", "identifier": "GP-01", "name": "Grille piéton"},
        ]
        
        for eq_data in common_equipments:
            service_type = service_types[eq_data["type"]]
            equipment = ServiceInstance(
                copro_id=copro.id,
                building_id=building_common.id,
                service_type_id=service_type.id,
                name=eq_data["name"],
                identifier=eq_data["identifier"],
                description=f"{eq_data['type']} - Équipement commun",
                status="operational",
                order=order_counter,
                is_active=True
            )
            db.add(equipment)
            order_counter += 1
            print(f"  ✅ {eq_data['name']} ({eq_data['identifier']})")
        
        # 9. Commit final
        db.commit()
        
        print("\n" + "="*60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("="*60)
        print(f"Copropriété: {copro.name}")
        print(f"Bâtiments: {len(buildings)}")
        print(f"Types de services: {len(service_types)}")
        total_equipments = db.query(ServiceInstance).filter(ServiceInstance.copro_id == copro.id).count()
        print(f"Équipements: {total_equipments}")
        print("="*60)
        print("\n📝 Compte admin:")
        print("   Username: admin")
        print("   Password: admin123")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    # Initialiser les données de test
    init_test_data()

