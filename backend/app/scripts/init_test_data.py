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
from app.models.copro import Copro, Building, ServiceInstance
from app.models.user import User
from app.models.ticket import Ticket
from app.models.status import Incident, IncidentUpdate, IncidentComment
import bcrypt


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_admin_if_not_exists(db):
    """Créer un compte admin s'il n'existe pas"""
    existing_admin = db.query(User).filter(User.email == "admin@admin.com").first()
    if existing_admin:
        print("ℹ️  Compte admin existe déjà")
        # S'assurer que le compte est actif et admin
        existing_admin.is_superuser = True
        existing_admin.is_active = True
        db.commit()
        return existing_admin
    
    admin = User(
        email="admin@admin.com",
        hashed_password=get_password_hash("admin123"),
        is_superuser=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print("✅ Compte admin créé (email: admin@admin.com, password: admin123)")
    return admin


def init_test_data():
    """Initialiser les données de test"""
    db = SessionLocal()
    
    try:
        # 1. Créer le compte admin si nécessaire
        create_admin_if_not_exists(db)
        
        # 2. Vérifier si une copropriété existe déjà et la supprimer pour réinitialiser
        existing_copro = db.query(Copro).filter(Copro.is_active == True).first()
        if existing_copro:
            print("⚠️  Une copropriété existe déjà. Suppression des données existantes pour réinitialisation...")
            copro_id = existing_copro.id
            
            # Supprimer dans l'ordre pour respecter les contraintes de clés étrangères
            
            # 1. Supprimer les commentaires d'incidents
            incidents = db.query(Incident).filter(Incident.copro_id == copro_id).all()
            incident_ids = [inc.id for inc in incidents]
            if incident_ids:
                db.query(IncidentComment).filter(IncidentComment.incident_id.in_(incident_ids)).delete()
                db.query(IncidentUpdate).filter(IncidentUpdate.incident_id.in_(incident_ids)).delete()
                print(f"  ✅ Supprimé {len(incident_ids)} incidents et leurs commentaires/mises à jour")
            
            # 2. Supprimer les incidents
            db.query(Incident).filter(Incident.copro_id == copro_id).delete()
            
            # 3. Supprimer les tickets
            tickets_count = db.query(Ticket).filter(Ticket.copro_id == copro_id).count()
            db.query(Ticket).filter(Ticket.copro_id == copro_id).delete()
            if tickets_count > 0:
                print(f"  ✅ Supprimé {tickets_count} tickets")
            
            # 4. Mettre à NULL les références aux bâtiments dans les utilisateurs (sauf admin)
            users_updated = db.query(User).filter(
                User.copro_id == copro_id,
                User.email != "admin@admin.com"  # Garder l'admin
            ).update({"building_id": None, "copro_id": None}, synchronize_session=False)
            if users_updated > 0:
                print(f"  ✅ Détaché {users_updated} utilisateurs de la copropriété")
            
            # 5. Supprimer les équipements (ServiceInstance)
            equipments_count = db.query(ServiceInstance).filter(ServiceInstance.copro_id == copro_id).count()
            db.query(ServiceInstance).filter(ServiceInstance.copro_id == copro_id).delete()
            if equipments_count > 0:
                print(f"  ✅ Supprimé {equipments_count} équipements")
            
            # 6. Supprimer les bâtiments
            buildings_count = db.query(Building).filter(Building.copro_id == copro_id).count()
            db.query(Building).filter(Building.copro_id == copro_id).delete()
            if buildings_count > 0:
                print(f"  ✅ Supprimé {buildings_count} bâtiments")
            
            # 8. Supprimer la copropriété
            db.delete(existing_copro)
            db.commit()
            print("✅ Toutes les données existantes ont été supprimées")
        
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
        
        # 4. Créer les 2 bâtiments
        buildings_data = [
            {"name": "Bâtiment A", "description": "Premier bâtiment", "order": 1},
            {"name": "Bâtiment B", "description": "Deuxième bâtiment", "order": 2},
        ]
        
        buildings = {}
        for b_data in buildings_data:
            building = Building(
                copro_id=copro.id,
                name=b_data["name"],
                description=b_data["description"],
                order=b_data["order"],
                is_active=True
            )
            db.add(building)
            db.flush()
            buildings[b_data["name"]] = building
            print(f"✅ Bâtiment créé: {building.name} (ID: {building.id})")
        
        # 5. Créer les équipements pour chaque bâtiment
        building_equipments = [
            {"name": "Ascenseur", "count": 2, "prefix": "ASC"},
            {"name": "Eau chaude", "count": 1, "prefix": "EC"},
            {"name": "Eau froide", "count": 1, "prefix": "EF"},
            {"name": "Électricité", "count": 1, "prefix": "ELEC"},
            {"name": "Éclairage", "count": 1, "prefix": "LUM"},
            {"name": "Porte d'entrée", "count": 1, "prefix": "PE"},
        ]
        
        order_counter = 1
        for building_name, building in buildings.items():
            print(f"\n📦 Création des équipements pour le bâtiment {building_name}:")
            for eq_config in building_equipments:
                for i in range(eq_config["count"]):
                    if eq_config["count"] > 1:
                        # Utiliser un identifiant basé sur le nom du bâtiment pour rendre le nom unique dans la DB
                        building_short = building_name.replace("Bâtiment ", "").replace(" ", "")
                        identifier = f"{eq_config['prefix']}-{building_short}-{i+1:02d}"
                        name = f"{eq_config['name']} {i+1} ({identifier})"
                    else:
                        building_short = building_name.replace("Bâtiment ", "").replace(" ", "")
                        identifier = f"{eq_config['prefix']}-{building_short}"
                        name = f"{eq_config['name']} ({identifier})"
                    
                    equipment = ServiceInstance(
                        copro_id=copro.id,
                        building_id=building.id,
                        name=name,
                        identifier=identifier,
                        description=None,
                        status="operational",
                        order=order_counter,
                        is_active=True
                    )
                    db.add(equipment)
                    order_counter += 1
                    # Afficher sans l'identifier pour la lisibilité
                    display_name = f"{eq_config['name']} {i+1}" if eq_config["count"] > 1 else f"{eq_config['name']}"
                    print(f"  ✅ {display_name} ({identifier})")
        
        # 6. Créer un bâtiment "Commun" pour les équipements partagés
        building_common = Building(
            copro_id=copro.id,
            name="Équipements communs",
            description="Équipements partagés entre tous les bâtiments",
            order=99,
            is_active=True
        )
        db.add(building_common)
        db.flush()
        print(f"\n✅ Bâtiment commun créé: {building_common.name} (ID: {building_common.id})")
        
        # 7. Créer les équipements communs
        print(f"\n📦 Création des équipements communs:")
        common_equipments = [
            {"name": "Porte parking", "identifier": "PP-01"},
            {"name": "Grille voiture", "identifier": "GV-01"},
            {"name": "Grille piéton", "identifier": "GP-01"},
        ]
        
        for eq_data in common_equipments:
            # Ajouter l'identifier au nom pour garantir l'unicité en base
            db_name = f"{eq_data['name']} ({eq_data['identifier']})"
            equipment = ServiceInstance(
                copro_id=copro.id,
                building_id=building_common.id,
                name=db_name,
                identifier=eq_data["identifier"],
                description=None,
                status="operational",
                order=order_counter,
                is_active=True
            )
            db.add(equipment)
            order_counter += 1
            print(f"  ✅ {eq_data['name']} ({eq_data['identifier']})")
        
        # 8. Commit final
        db.commit()
        
        print("\n" + "="*60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("="*60)
        print(f"Copropriété: {copro.name}")
        print(f"Bâtiments: {len(buildings) + 1}")  # +1 pour le bâtiment commun
        total_equipments = db.query(ServiceInstance).filter(ServiceInstance.copro_id == copro.id).count()
        print(f"Équipements: {total_equipments}")
        print("="*60)
        print("\n📝 Compte admin:")
        print("   Email: admin@admin.com")
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

