# Structure de Données pour les Copropriétés

## Vue d'ensemble

Cette structure permet de gérer facilement l'instanciation des éléments d'une copropriété de manière modulaire et extensible.

## Modèles de Données

### 1. Copro (Copropriété)
**Table**: `copros`

Entité principale multi-tenant. Chaque copropriété est isolée.

**Champs**:
- `id`: Identifiant unique
- `name`: Nom de la copropriété
- `address`, `city`, `postal_code`, `country`: Adresse
- `is_active`: Actif/inactif
- `created_at`, `updated_at`: Métadonnées

**Relations**:
- `buildings`: Liste des bâtiments
- `service_types`: Types de services disponibles
- `users`: Utilisateurs associés

### 2. Building (Bâtiment)
**Table**: `buildings`

Représente un bâtiment dans une copropriété (A, B, 1, 2, etc.)

**Champs**:
- `id`: Identifiant unique
- `copro_id`: Référence à la copropriété
- `identifier`: Identifiant du bâtiment (A, B, 1, 2, etc.) - **unique par copropriété**
- `name`: Nom optionnel (ex: "Bâtiment Principal")
- `description`: Description
- `order`: Ordre d'affichage
- `is_active`: Actif/inactif

**Contrainte unique**: `(copro_id, identifier)` - Un identifiant unique par copropriété

**Relations**:
- `copro`: Copropriété parente
- `service_instances`: Instances de services dans ce bâtiment

### 3. ServiceType (Type de Service)
**Table**: `service_types`

Template réutilisable pour définir les types d'équipements disponibles dans une copropriété.

**Champs**:
- `id`: Identifiant unique
- `copro_id`: Référence à la copropriété
- `name`: Nom du type (ex: "Ascenseur", "Éclairage", "Eau chaude")
- `description`: Description
- `icon`: Icône/emoji (ex: "🚁", "💡")
- `category`: Catégorie (ex: "Équipement", "Fluide", "Sécurité")
- `default_status`: Status par défaut ("operational")
- `order`: Ordre d'affichage

**Exemples de types**:
- Ascenseur
- Éclairage
- Eau chaude
- Eau froide
- Porte parking
- Chauffage
- Interphone
- Vidéosurveillance

### 4. ServiceInstance (Instance de Service)
**Table**: `service_instances`

Instance réelle d'un service dans un bâtiment spécifique.

**Champs**:
- `id`: Identifiant unique
- `copro_id`: Référence à la copropriété
- `building_id`: Référence au bâtiment
- `service_type_id`: Référence au type de service
- `name`: Nom spécifique (ex: "Ascenseur Bâtiment A")
- `identifier`: Identifiant optionnel (ex: "ASC-A-01")
- `description`: Description
- `location`: Localisation précise (ex: "Rez-de-chaussée")
- `status`: Status actuel ("operational", "degraded", etc.)
- `order`: Ordre d'affichage

**Contrainte unique**: `(copro_id, name)` - Un nom unique par copropriété

**Relations**:
- `building`: Bâtiment parent
- `service_type`: Type de service
- `incidents`: Incidents liés

## Structure de Fichiers

```
backend/app/
├── models/
│   ├── copro.py          # Modèles Copro, Building, ServiceType, ServiceInstance
│   ├── status.py         # Modèles Service, Incident (mis à jour pour multi-tenant)
│   └── user.py           # Modèle User (mis à jour avec copro_id)
├── api/
│   └── endpoints/
│       ├── copro.py      # API CRUD pour copropriétés, bâtiments, services
│       ├── status.py     # API status page (public)
│       └── ...
└── scripts/
    └── seed_copro.py     # Script pour créer facilement une copropriété
```

## Exemple d'Instanciation

### Via l'API

```python
# 1. Créer une copropriété
POST /api/v1/copro/copros
{
  "name": "Résidence Les Jardins",
  "address": "123 Avenue de la République",
  "city": "Paris",
  "postal_code": "75011"
}

# 2. Créer des bâtiments
POST /api/v1/copro/buildings
{
  "copro_id": 1,
  "identifier": "A",
  "name": "Bâtiment A"
}

POST /api/v1/copro/buildings
{
  "copro_id": 1,
  "identifier": "B",
  "name": "Bâtiment B"
}

# 3. Créer des types de services
POST /api/v1/copro/service-types
{
  "copro_id": 1,
  "name": "Ascenseur",
  "icon": "🚁",
  "category": "Équipement"
}

POST /api/v1/copro/service-types
{
  "copro_id": 1,
  "name": "Éclairage",
  "icon": "💡",
  "category": "Équipement"
}

# 4. Créer des instances de services
POST /api/v1/copro/service-instances
{
  "copro_id": 1,
  "building_id": 1,
  "service_type_id": 1,
  "name": "Ascenseur - Bâtiment A",
  "identifier": "ASC-A-01"
}
```

### Via le Script de Seed

```bash
# Créer une copropriété d'exemple avec tout configuré
cd backend
python -m app.scripts.seed_copro
```

Le script crée automatiquement:
- 1 copropriété
- 3 bâtiments (A, B, C)
- 6 types de services (Ascenseur, Éclairage, Eau chaude, Eau froide, Porte parking, Chauffage)
- 18 instances de services (6 types × 3 bâtiments)

## Avantages de cette Structure

1. **Modularité**: Chaque copropriété est isolée (multi-tenant)
2. **Flexibilité**: Types de services configurables par copropriété
3. **Extensibilité**: Facile d'ajouter de nouveaux types ou bâtiments
4. **Réutilisabilité**: Les types de services sont des templates réutilisables
5. **Traçabilité**: Chaque service est lié à un bâtiment spécifique
6. **Organisation**: Support de catégories et ordre d'affichage

## Cas d'Usage

### Copropriété avec 2 bâtiments (A et B)
- Bâtiment A: Ascenseur, Éclairage, Eau chaude
- Bâtiment B: Ascenseur, Éclairage, Eau chaude, Porte parking

### Copropriété avec 3 bâtiments (1, 2, 3)
- Tous les bâtiments: Ascenseur, Chauffage
- Bâtiment 1 uniquement: Porte parking

### Ajout d'un nouveau type de service
1. Créer le `ServiceType` pour la copropriété
2. Créer les `ServiceInstance` pour chaque bâtiment concerné

## Intégration avec le Status Page

Les `ServiceInstance` peuvent être utilisés dans la page de statut publique:
- Afficher le statut de chaque service par bâtiment
- Filtrer par bâtiment
- Grouper par type de service

## Prochaines Étapes

- [ ] Interface admin pour gérer les copropriétés
- [ ] Import/Export de configuration
- [ ] Templates de copropriétés prédéfinis
- [ ] API pour dupliquer une configuration de copropriété



