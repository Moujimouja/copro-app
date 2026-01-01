# Scripts d'initialisation

## Scripts disponibles

### `init_test_data.py`

Script d'initialisation des données de test pour l'application.

**Ce qui est créé :**
- 1 copropriété de test ("Copropriété de Test")
- 1 compte administrateur (email: `admin@admin.com`, password: `admin123`)
- 2 bâtiments (A et B)
- 9 types de services :
  - Ascenseur
  - Éclairage
  - Eau chaude
  - Eau froide
  - Porte parking
  - Électricité
  - Porte d'entrée
  - Grille voiture
  - Grille piéton
- 17 équipements :
  - **Bâtiment A** : 2 ascenseurs, eau chaude, eau froide, électricité, éclairage, porte d'entrée
  - **Bâtiment B** : 2 ascenseurs, eau chaude, eau froide, électricité, éclairage, porte d'entrée
  - **Commun** : porte parking, grille voiture, grille piéton

**Utilisation :**

1. **Manuellement** :
   ```bash
   docker compose exec backend python -m app.scripts.init_test_data
   ```

2. **Automatiquement au démarrage** :
   Le script s'exécute automatiquement si la variable d'environnement `INIT_TEST_DATA=true` est définie dans `docker-compose.yml` (déjà configuré).

**Note :** Si une copropriété existe déjà, elle sera supprimée avec toutes ses données avant de créer les nouvelles données de test.

### `create_admin.py`

Script pour créer un compte administrateur.

**Utilisation :**
```bash
docker compose exec backend python -m app.scripts.create_admin
```

**Note :** Si un compte admin existe déjà avec l'email `admin@admin.com`, le mot de passe sera réinitialisé à `admin123`.

