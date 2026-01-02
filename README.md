# Copro App

Application web moderne pour la gestion d'une copropriété, avec interface d'administration et pages publiques pour le suivi du statut des équipements et la déclaration d'incidents.

## 🏗️ Architecture

Ce projet suit une structure monorepo avec des services backend et frontend séparés :

```
copro-app/
 ├─ backend/          # Application FastAPI backend
 ├─ frontend/         # Application React frontend
 ├─ docker-compose.yml
 └─ docs/             # Documentation du projet
```

## 🚀 Démarrage rapide

### Prérequis

- Docker et Docker Compose installés
- Node.js 18+ (pour le développement frontend local)
- Python 3.11+ (pour le développement backend local)

### Exécution avec Docker Compose

1. Cloner le dépôt et naviguer vers le répertoire du projet :
   ```bash
   cd copro-app
   ```

2. Démarrer tous les services :
   ```bash
   docker-compose up --build
   ```

3. Accéder à l'application :
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Documentation API: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

### Exécution des services localement

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

**Note:** Assurez-vous que PostgreSQL est en cours d'exécution (via Docker Compose ou localement) avant de démarrer le backend.

## 📁 Structure du projet

### Backend

- `app/main.py` - Point d'entrée de l'application FastAPI
- `app/api/endpoints/` - Gestionnaires de routes API
  - `admin.py` - Endpoints réservés aux administrateurs (équipements, incidents, tickets, maintenances)
  - `auth.py` - Authentification (login, register)
  - `public.py` - Endpoints publics (création de tickets, liste des services)
  - `status.py` - Données de la page de statut (publique)
- `app/core/` - Configuration et paramètres de base
- `app/models/` - Modèles de base de données SQLAlchemy
  - `copro.py` - Copro, Building, ServiceInstance
  - `status.py` - Incident, IncidentUpdate, IncidentComment, ServiceStatus enums
  - `ticket.py` - Ticket, TicketStatus, TicketType
  - `ticket_comment.py` - TicketComment (commentaires des admins sur les tickets)
  - `user.py` - User (avec copro_id, is_superuser)
  - `maintenance.py` - Maintenance (maintenances planifiées)
- `app/db.py` - Connexion à la base de données et gestion des sessions
- `app/auth.py` - Utilitaires d'authentification et d'autorisation
- `app/scripts/` - Scripts utilitaires
  - `init_test_data.py` - Initialisation des données de test
  - `migrate_ticket_type.py` - Migration pour ajouter le type de ticket
  - `migrate_ticket_status.py` - Migration pour mettre à jour les statuts de ticket

### Frontend

- `src/App.jsx` - Composant principal de l'application React avec routage et header sticky avec menu burger
- `src/Admin.jsx` - Interface d'administration (gestion des équipements, tickets, incidents, maintenances, utilisateurs)
- `src/Status.jsx` - Page de statut publique (affichage des équipements, incidents, maintenances)
- `src/ReportIncident.jsx` - Formulaire public de déclaration d'incident/demande
- `src/Expenses.jsx` - Suivi des dépenses
- `src/main.jsx` - Point d'entrée React

## ✨ Fonctionnalités principales

### Pages publiques

1. **Page de statut** (`/status`)
   - Affichage du statut global de la copropriété
   - Liste des équipements par bâtiment avec leur statut
   - Affichage des incidents en cours et de l'historique
   - Affichage des maintenances planifiées
   - Design moderne avec image circulaire de la copropriété
   - Bâtiments avec tous les services opérationnels fermés par défaut

2. **Déclaration d'incident/demande** (`/report`)
   - Formulaire pour créer un ticket (Incident ou Demande)
   - Validation complète des champs avec messages d'erreur clairs
   - Champs conditionnels selon le type (équipement obligatoire pour les incidents)
   - Téléphone optionnel

3. **Suivi des dépenses** (`/expenses`)
   - Visualisation des dépenses de la copropriété

### Interface d'administration (`/admin`)

1. **Gestion de la copropriété**
   - Création et modification des informations de la copropriété
   - Affichage moderne avec image circulaire

2. **Gestion des équipements**
   - CRUD complet des équipements (ServiceInstance)
   - Modification du statut des équipements
   - Association aux bâtiments

3. **Gestion des bâtiments**
   - CRUD complet des bâtiments
   - Ordre d'affichage personnalisable

4. **Gestion des tickets** ("Demande à traiter")
   - Liste des tickets avec compteur des tickets non clos
   - Workflow de statut : En cours d'analyse → En cours de traitement → Résolu → Clos
   - Ajout de commentaires par les administrateurs
   - Conversion de tickets en incidents (avec transfert des commentaires)
   - Affichage du type (Incident ou Demande)

5. **Gestion des incidents**
   - Liste des incidents avec compteur des incidents non clos
   - Édition du titre, description et équipement concerné
   - Modification du statut
   - Ajout de commentaires
   - Ajout de mises à jour

6. **Gestion des maintenances**
   - Création et modification des maintenances planifiées
   - Association à plusieurs équipements
   - Dates de début et de fin

7. **Gestion des utilisateurs**
   - Liste des utilisateurs
   - Gestion des rôles (admin)

### Workflow des tickets

1. **Création** : Un utilisateur public crée un ticket (Incident ou Demande)
2. **Analyse** : Statut initial "En cours d'analyse"
3. **Traitement** : L'admin peut changer le statut en "En cours de traitement"
4. **Résolution** : Une fois traité, le statut passe à "Résolu"
5. **Clôture** : Finalement, le statut passe à "Clos"
6. **Conversion** : Un ticket peut être converti en incident officiel

## 🔐 Authentification

L'application utilise l'authentification JWT :

- **Inscription** : `POST /api/v1/auth/register`
- **Connexion** : `POST /api/v1/auth/login`
- **Utilisateur actuel** : `GET /api/v1/auth/me` (nécessite une authentification)

### Rôles

- **Administrateur** : Accès complet à l'interface d'administration (`is_superuser = True`)
- **Public** : Accès aux pages publiques (statut, déclaration d'incident)

## 📊 Modèles de données

### Copro
- Informations de la copropriété (nom, adresse, ville, code postal, pays)

### Building
- Bâtiments de la copropriété (A, B, 1, 2, etc.)
- Ordre d'affichage personnalisable

### ServiceInstance
- Équipements réels dans les bâtiments
- Statuts : operational, degraded, partial_outage, major_outage, maintenance
- Association à un bâtiment

### Ticket
- Déclarations d'incidents/demandes créées par le public
- Types : INCIDENT, REQUEST
- Statuts : analyzing, in_progress, resolved, closed
- Champs : titre, description, équipement concerné (optionnel pour les demandes), localisation, informations du déclarant

### TicketComment
- Commentaires des administrateurs sur les tickets
- Transférés automatiquement lors de la conversion en incident

### Incident
- Incidents officiels créés par les administrateurs
- Statuts : investigating, in_progress, resolved, closed
- Peut être créé depuis un ticket ou directement
- Association à un équipement

### IncidentUpdate
- Mises à jour sur les incidents (changements de statut, messages)

### IncidentComment
- Commentaires des administrateurs sur les incidents

### Maintenance
- Maintenances planifiées
- Dates de début et de fin
- Association à plusieurs équipements

### User
- Utilisateurs du système
- `is_superuser` pour les administrateurs
- Association à une copropriété (`copro_id`)

## 🛠️ Développement

### Variables d'environnement

Créer un fichier `.env` dans le répertoire `backend/` pour le développement local :

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coproapp
SECRET_KEY=your-secret-key-here
```

### Migrations de base de données

L'application utilise SQLAlchemy avec création automatique des tables. Pour la production, envisager d'utiliser Alembic pour les migrations.

Des scripts de migration manuels sont disponibles dans `backend/app/scripts/` :
- `migrate_ticket_type.py` - Ajoute le type de ticket
- `migrate_ticket_status.py` - Met à jour les statuts de ticket

### Documentation API

FastAPI génère automatiquement une documentation interactive :
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Scripts disponibles

- **Initialiser les données de test** : `python -m app.scripts.init_test_data`
  - Crée une copropriété avec des bâtiments, équipements et données de test
  - Crée un utilisateur admin (email: admin@example.com, password: admin123)

## 🎨 Interface utilisateur

### Design responsive
- Menu burger sur mobile
- Header sticky qui reste fixé en haut lors du scroll
- Design moderne avec gradients et ombres
- Animations au survol

### Validation des formulaires
- Validation côté client avec messages d'erreur clairs
- Validation côté serveur avec gestion d'erreurs robuste
- Champs conditionnels selon le contexte

## 📚 Documentation

- [Architecture](./docs/ARCHITECTURE.md) - Vue d'ensemble de l'architecture système
- [Decisions](./docs/DECISIONS.md) - Enregistrements de décisions architecturales
- [Roadmap](./docs/ROADMAP.md) - Feuille de route du projet et plans futurs

## 🧪 Tests

```bash
# Tests backend (à implémenter)
cd backend
pytest

# Tests frontend (à implémenter)
cd frontend
npm test
```

## 📝 Licence

[À ajouter]
