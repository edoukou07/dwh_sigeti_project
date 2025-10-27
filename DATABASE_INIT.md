# Initialisation de la Base de Données SIGETI

Ce document décrit le processus d'initialisation automatique de la base de données pour le projet SIGETI DWH.

## 📋 Vue d'ensemble

L'initialisation de la base de données est maintenant automatisée et intégrée au début du pipeline ETL. Elle comprend :

- Création de la base de données `sigeti_dwh`
- Création de l'utilisateur `sigeti_user` avec les permissions appropriées
- Configuration des schémas (`staging`, `marts`, `analytics`)
- Installation des extensions PostgreSQL nécessaires

## 🔄 Initialisation Automatique

### Dans le Pipeline Airflow

L'initialisation est automatiquement exécutée au début de chaque DAG via la tâche `initialize_database`. Cette tâche :

- Vérifie si la base et l'utilisateur existent déjà
- Crée uniquement les éléments manquants (idempotente)
- Configure les permissions et schémas nécessaires
- Valide la configuration avant de passer aux tâches suivantes

### Configuration via Variables Airflow

Les paramètres peuvent être personnalisés via les variables Airflow :

```bash
# Configuration de la base PostgreSQL
sigeti_node_host=host.docker.internal      # Adresse du serveur PostgreSQL
sigeti_node_port=5432                      # Port du serveur PostgreSQL
sigeti_node_user=postgres                  # Utilisateur administrateur
sigeti_node_password=postgres              # Mot de passe administrateur

# Configuration de la base SIGETI
sigeti_db_name=sigeti_dwh                  # Nom de la base SIGETI
sigeti_db_user=sigeti_user                 # Utilisateur SIGETI
sigeti_db_password=sigeti123               # Mot de passe utilisateur SIGETI
```

## 🛠️ Initialisation Manuelle

### Méthode 1: Script PowerShell (Windows)

```powershell
# Initialisation complète
.\docker-sigeti.ps1 init-db

# Test de l'initialisation
.\docker-sigeti.ps1 test-init
```

### Méthode 2: Makefile (Linux/Mac)

```bash
# Initialisation complète
make init-db

# Test de l'initialisation
make test-init
```

### Méthode 3: Scripts Python Direct

```bash
# Initialisation
python scripts/init_database.py

# Test complet
python scripts/test_database_init.py
```

### Méthode 4: Script Bash (Docker)

```bash
# Dans un conteneur Docker
chmod +x scripts/init_database.sh
./scripts/init_database.sh
```

## 📊 Scripts Disponibles

### `init_database.py`
Script Python principal d'initialisation avec classe `DatabaseInitializer` :

- **Fonctionnalités** : Création DB/utilisateur, permissions, schémas, tests
- **Configuration** : Variables d'environnement ou valeurs par défaut
- **Sécurité** : Vérifications d'existence, gestion d'erreurs robuste
- **Logging** : Messages détaillés pour debug et monitoring

### `init_database.sql`
Script SQL pur pour initialisation manuelle :

- **Contenu** : Extensions, schémas, utilisateurs, permissions
- **Usage** : `psql -f scripts/init_database.sql`
- **Avantages** : Rapide, léger, standard PostgreSQL

### `init_database.sh`
Script Bash pour environnement Docker/Linux :

- **Intégration** : Variables d'environnement Docker
- **Robustesse** : Vérifications et retry automatique
- **Logs** : Format standardisé pour monitoring

### `test_database_init.py`
Suite de tests complète :

- **Tests** : Connexion admin, existence DB/user, permissions, schémas
- **Rapport** : Résultats détaillés avec codes couleur
- **Exit codes** : 0 = succès, 1 = échec

### `test-database.ps1`
Interface PowerShell pour les tests :

- **Configuration** : Paramètres personnalisables
- **Dépendances** : Installation automatique de psycopg2
- **Intégration** : Appel du script Python avec gestion d'erreurs

## 🔧 Configuration des Variables d'Environnement

### Variables Principales

| Variable | Description | Défaut |
|----------|-------------|---------|
| `SIGETI_NODE_HOST` | Adresse serveur PostgreSQL | `localhost` |
| `SIGETI_NODE_PORT` | Port serveur PostgreSQL | `5432` |
| `SIGETI_NODE_USER` | Utilisateur admin PostgreSQL | `postgres` |
| `SIGETI_NODE_PASSWORD` | Mot de passe admin | `postgres` |
| `SIGETI_DB_NAME` | Nom base SIGETI | `sigeti_dwh` |
| `SIGETI_DB_USER` | Utilisateur SIGETI | `sigeti_user` |
| `SIGETI_DB_PASSWORD` | Mot de passe SIGETI | `sigeti123` |

### Configuration Docker Compose

Dans `docker-compose.yml`, les services utilisent `host.docker.internal` pour accéder aux bases locales :

```yaml
environment:
  - SIGETI_NODE_HOST=host.docker.internal
  - SIGETI_NODE_DB_HOST=host.docker.internal
```

### Configuration Airflow

Variables à définir dans l'interface Airflow Admin > Variables :

```json
{
  "sigeti_node_host": "host.docker.internal",
  "sigeti_node_port": "5432",
  "sigeti_node_user": "postgres",
  "sigeti_node_password": "postgres",
  "sigeti_db_name": "sigeti_dwh",
  "sigeti_db_user": "sigeti_user",
  "sigeti_db_password": "sigeti123"
}
```

## 🧪 Tests et Validation

### Tests Automatiques

Le script `test_database_init.py` effectue une batterie complète de tests :

1. **Test de connexion administrateur**
   - Vérification de l'accès PostgreSQL avec compte admin
   
2. **Test d'existence de la base de données**
   - Contrôle de l'existence de `sigeti_dwh`
   
3. **Test d'existence de l'utilisateur**
   - Vérification de l'utilisateur `sigeti_user`
   
4. **Test de connexion utilisateur**
   - Validation de l'accès avec compte SIGETI
   
5. **Test des permissions**
   - Vérification des droits CREATE, INSERT, SELECT, DROP
   
6. **Test des schémas**
   - Contrôle de l'existence des schémas `staging`, `marts`, `analytics`

### Codes de Sortie

- `0` : Tous les tests réussis ✅
- `1` : Un ou plusieurs tests échoués ❌

### Exemple de Sortie

```
============================================================
🧪 TESTS D'INITIALISATION BASE DE DONNÉES SIGETI
============================================================

📋 Configuration:
  NODE_HOST: localhost
  NODE_PORT: 5432
  NODE_USER: postgres
  NODE_PASSWORD: ********
  SIGETI_DB: sigeti_dwh
  SIGETI_USER: sigeti_user
  SIGETI_PASSWORD: ********

========================================
TEST 1: Connexion Administrateur
========================================
🔍 Test de connexion administrateur...
✅ Connexion administrateur réussie

========================================
TEST 2: Base de Données
========================================
🔍 Vérification de l'existence de la base 'sigeti_dwh'...
✅ Base de données 'sigeti_dwh' existe

... [autres tests]

============================================================
🎯 RÉSUMÉ DES TESTS
============================================================
✅ TOUS LES TESTS RÉUSSIS
🚀 Base de données prête pour le pipeline SIGETI
```

## 🔍 Dépannage

### Problèmes Courants

#### 1. Erreur de connexion PostgreSQL

**Symptôme** : `could not connect to server`

**Solutions** :
```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql  # Linux
Get-Service postgresql*           # Windows

# Vérifier la configuration de connexion
telnet localhost 5432
```

#### 2. Permissions insuffisantes

**Symptôme** : `permission denied for database`

**Solutions** :
```sql
-- Se connecter en tant que postgres
ALTER USER sigeti_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE sigeti_dwh TO sigeti_user;
```

#### 3. Base de données déjà existante

**Symptôme** : `database "sigeti_dwh" already exists`

**Action** : Normal, le script est idempotent et ignore cette erreur

#### 4. psycopg2 non disponible

**Symptôme** : `ModuleNotFoundError: No module named 'psycopg2'`

**Solutions** :
```bash
# Installation basique
pip install psycopg2-binary

# Ou avec conda
conda install psycopg2

# En cas d'erreur de compilation
sudo apt-get install libpq-dev python3-dev  # Ubuntu/Debian
```

### Logs et Monitoring

#### Logs Airflow
```bash
# Voir les logs de la tâche d'initialisation
docker-compose logs airflow-scheduler | grep initialize_database
```

#### Logs PostgreSQL
```bash
# Logs de connexion (Ubuntu/Debian)
sudo tail -f /var/log/postgresql/postgresql-*.log

# Logs de connexion (CentOS/RHEL)
sudo tail -f /var/lib/pgsql/data/log/postgresql-*.log
```

#### Debug Avancé

Pour debug les problèmes de connexion :

```python
# Test de connexion direct
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='postgres',
    user='postgres',
    password='postgres'
)
print("Connexion réussie !")
conn.close()
```

### Variables de Debug

Activer le mode debug :

```bash
export SIGETI_DEBUG=1
python scripts/init_database.py
```

## 🚀 Intégration Continue

### Workflow Recommandé

1. **Développement local** :
   ```bash
   # Test rapide
   make test-init
   
   # Initialisation si nécessaire
   make init-db
   ```

2. **Déploiement Docker** :
   ```bash
   # Stack complète
   ./docker-sigeti.ps1 up
   
   # Le pipeline démarre avec initialisation automatique
   ```

3. **Production** :
   - L'initialisation fait partie du DAG
   - Surveillance via Airflow UI
   - Alertes en cas d'échec

### Bonnes Pratiques

1. **Toujours tester** avant déploiement
2. **Sauvegarder** avant initialisation en production
3. **Monitorer** les logs d'initialisation
4. **Documenter** les changements de schéma

Cette documentation assure une initialisation robuste et reproductible de l'environnement SIGETI DWH.