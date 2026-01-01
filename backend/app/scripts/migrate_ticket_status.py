"""
Script de migration pour mettre à jour l'enum ticketstatus
Usage: python -m app.scripts.migrate_ticket_status
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import SessionLocal
from sqlalchemy import text

def migrate_ticket_status():
    """Mettre à jour l'enum ticketstatus pour correspondre au nouveau modèle"""
    db = SessionLocal()
    try:
        print("🔄 Migration de l'enum ticketstatus...")
        
        # Vérifier les valeurs actuelles
        result = db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'ticketstatus')
            ORDER BY enumsortorder
        """))
        current_values = [row[0] for row in result.fetchall()]
        print(f"  Valeurs actuelles: {current_values}")
        
        # Nouvelles valeurs attendues
        new_values = ['ANALYZING', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']
        
        if set(current_values) == set(new_values):
            print("✅ L'enum ticketstatus est déjà à jour")
            return
        
        # Sauvegarder les données existantes
        print("🔄 Sauvegarde des données existantes...")
        db.execute(text("""
            ALTER TABLE tickets ADD COLUMN IF NOT EXISTS status_backup TEXT;
            UPDATE tickets SET status_backup = status::text;
        """))
        db.commit()
        
        # Supprimer l'ancien type et créer le nouveau
        print("🔄 Création du nouveau type enum...")
        db.execute(text("""
            -- Supprimer l'ancien type (cascade pour supprimer la colonne temporairement)
            DROP TYPE IF EXISTS ticketstatus_old CASCADE;
            
            -- Renommer l'ancien type
            ALTER TYPE ticketstatus RENAME TO ticketstatus_old;
        """))
        db.commit()
        
        # Créer le nouveau type
        db.execute(text("""
            CREATE TYPE ticketstatus AS ENUM ('ANALYZING', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
        """))
        db.commit()
        
        # Recréer la colonne avec le nouveau type
        print("🔄 Mise à jour de la colonne status...")
        db.execute(text("""
            ALTER TABLE tickets 
            ALTER COLUMN status TYPE ticketstatus 
            USING CASE 
                WHEN status_backup = 'PENDING' THEN 'ANALYZING'::ticketstatus
                WHEN status_backup = 'REVIEWING' THEN 'ANALYZING'::ticketstatus
                WHEN status_backup = 'APPROVED' THEN 'IN_PROGRESS'::ticketstatus
                WHEN status_backup = 'REJECTED' THEN 'CLOSED'::ticketstatus
                WHEN status_backup = 'RESOLVED' THEN 'RESOLVED'::ticketstatus
                WHEN status_backup IN ('analyzing', 'ANALYZING') THEN 'ANALYZING'::ticketstatus
                WHEN status_backup IN ('in_progress', 'IN_PROGRESS') THEN 'IN_PROGRESS'::ticketstatus
                WHEN status_backup IN ('resolved', 'RESOLVED') THEN 'RESOLVED'::ticketstatus
                WHEN status_backup IN ('closed', 'CLOSED') THEN 'CLOSED'::ticketstatus
                ELSE 'ANALYZING'::ticketstatus
            END;
        """))
        db.commit()
        
        # Supprimer la colonne de backup
        db.execute(text("""
            ALTER TABLE tickets DROP COLUMN IF EXISTS status_backup;
        """))
        db.commit()
        
        # Supprimer l'ancien type
        db.execute(text("""
            DROP TYPE IF EXISTS ticketstatus_old;
        """))
        db.commit()
        
        print("✅ Migration de l'enum ticketstatus terminée avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_ticket_status()

