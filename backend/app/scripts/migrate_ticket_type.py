"""
Script de migration pour ajouter la colonne 'type' à la table tickets
Usage: python -m app.scripts.migrate_ticket_type
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import engine, SessionLocal
from sqlalchemy import text

def migrate_ticket_type():
    """Ajouter la colonne type à la table tickets si elle n'existe pas"""
    db = SessionLocal()
    try:
        # Vérifier si la colonne existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tickets' AND column_name='type'
        """))
        
        if result.fetchone():
            print("✅ La colonne 'type' existe déjà dans la table tickets")
            return
        
        # Vérifier si le type ENUM existe et ses valeurs
        result = db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tickettype')
            ORDER BY enumsortorder
        """))
        enum_values = [row[0] for row in result.fetchall()]
        
        if not enum_values:
            # Créer le type ENUM si nécessaire (SQLAlchemy utilise les noms en majuscules)
            print("🔄 Création du type ENUM tickettype...")
            db.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE tickettype AS ENUM ('INCIDENT', 'REQUEST');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            db.commit()
            enum_values = ['INCIDENT', 'REQUEST']
        else:
            print(f"✅ Type ENUM tickettype existe déjà avec les valeurs: {enum_values}")
        
        # Ajouter la colonne type (sans DEFAULT d'abord, puis on met à jour)
        print("🔄 Ajout de la colonne 'type' à la table tickets...")
        db.execute(text("""
            ALTER TABLE tickets 
            ADD COLUMN IF NOT EXISTS type tickettype
        """))
        db.commit()
        
        # Mettre à jour les valeurs existantes (utiliser la première valeur de l'enum)
        default_value = enum_values[0] if enum_values else 'INCIDENT'
        print(f"🔄 Mise à jour des valeurs existantes avec '{default_value}'...")
        db.execute(text(f"""
            UPDATE tickets 
            SET type = '{default_value}'::tickettype
            WHERE type IS NULL
        """))
        db.commit()
        
        # Maintenant rendre la colonne NOT NULL
        db.execute(text(f"""
            ALTER TABLE tickets 
            ALTER COLUMN type SET NOT NULL,
            ALTER COLUMN type SET DEFAULT '{default_value}'::tickettype
        """))
        db.commit()
        
        print("✅ Colonne 'type' ajoutée avec succès")
        
        # Mettre à jour les statuts si nécessaire
        print("🔄 Mise à jour des statuts des tickets...")
        db.execute(text("""
            DO $$ BEGIN
                -- Supprimer l'ancien type si nécessaire
                DROP TYPE IF EXISTS ticketstatus CASCADE;
            EXCEPTION
                WHEN OTHERS THEN null;
            END $$;
        """))
        
        # Créer le nouveau type de statut
        db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE ticketstatus AS ENUM ('analyzing', 'in_progress', 'resolved', 'closed');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        db.commit()
        
        # Mettre à jour les statuts existants
        db.execute(text("""
            UPDATE tickets 
            SET status = CASE 
                WHEN status::text = 'pending' THEN 'analyzing'::ticketstatus
                WHEN status::text = 'reviewing' THEN 'analyzing'::ticketstatus
                WHEN status::text = 'approved' THEN 'in_progress'::ticketstatus
                WHEN status::text = 'rejected' THEN 'closed'::ticketstatus
                WHEN status::text = 'resolved' THEN 'resolved'::ticketstatus
                ELSE 'analyzing'::ticketstatus
            END
            WHERE status::text NOT IN ('analyzing', 'in_progress', 'resolved', 'closed')
        """))
        db.commit()
        
        # Modifier la colonne status pour utiliser le nouveau type
        print("🔄 Mise à jour de la colonne 'status'...")
        db.execute(text("""
            ALTER TABLE tickets 
            ALTER COLUMN status TYPE ticketstatus 
            USING status::text::ticketstatus
        """))
        db.commit()
        
        print("✅ Migration terminée avec succès")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_ticket_type()

