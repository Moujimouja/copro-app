"""
Script pour créer un compte administrateur de test
Usage: python -m app.scripts.create_admin
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal, engine, Base
from app.models.user import User
import bcrypt

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_admin():
    """Créer un compte administrateur de test"""
    db = SessionLocal()
    
    try:
        # Vérifier si l'admin existe déjà par email
        existing_admin = db.query(User).filter(User.email == "admin@admin.com").first()
        if existing_admin:
            print("⚠️  Un compte admin existe déjà avec l'email 'admin@admin.com'")
            print("   Réinitialisation du mot de passe...")
            existing_admin.hashed_password = get_password_hash("admin123")
            existing_admin.is_superuser = True
            existing_admin.is_active = True
            db.commit()
            print("✅ Mot de passe de l'admin réinitialisé")
            print(f"   Email: admin@admin.com")
            print(f"   Password: admin123")
            return
        
        # Créer le compte admin
        admin = User(
            email="admin@admin.com",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("="*50)
        print("✅ COMPTE ADMINISTRATEUR CRÉÉ")
        print("="*50)
        print(f"Email: admin@admin.com")
        print(f"Password: admin123")
        print("="*50)
        print("\n⚠️  IMPORTANT: Changez le mot de passe après la première connexion!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    # Créer l'admin
    create_admin()

