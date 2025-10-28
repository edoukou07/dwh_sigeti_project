# 🐳 SIGETI DWH - Configuration Docker

Cette documentation décrit la configuration Docker complète pour le projet SIGETI DWH, permettant de containeriser tous les composants sauf les bases de données qui restent locales.

## 📋 Architecture Docker

### 🏗️ **Services Déployés**
- **Airflow** : Orchestration ETL (webserver, scheduler, worker, flower)
- **dbt** : Transformations de données 

- **Grafana** : Monitoring et dashboards
- **Prometheus** : Collecte de métriques
- **Redis** : Queue Celery pour Airflow

### 🗄️ **Bases de Données (LOCAL)**
- **sigeti_dwh** : Base principale (port 5432)
- **sigeti_node_db** : Base source (port 5432) 
- **Connexion** : via `host.docker.internal` depuis les conteneurs

## 🚀 Démarrage Rapide

### ✅ **Prérequis**
```powershell
# Vérifier Docker
docker --version
docker-compose --version

# Vérifier les bases locales sont actives
psql -h localhost -U sigeti_user -d sigeti_dwh -c "SELECT 1;"
```

### 📋 **Installation Make sur Windows (optionnel)**
Pour utiliser les commandes `make` sur Windows :
```powershell
# Option 1: Via Chocolatey
choco install make

# Option 2: Via Scoop
scoop install make

# Option 3: WSL (recommandé pour développement)
wsl --install
```

### 🔨 **Construction et Démarrage**
```powershell
# Méthode 1: Script PowerShell (recommandé)
.\docker-sigeti.ps1 build
.\docker-sigeti.ps1 up

# Méthode 2: Docker Compose direct
docker-compose build --no-cache
docker-compose up -d
```

### 🌐 **URLs d'Accès**
Une fois démarré, accédez aux services :
- **Airflow** : http://localhost:8080 (admin/admin123)
- **Grafana** : http://localhost:3000 (admin/admin123) 

- **Flower** : http://localhost:5555
- **Prometheus** : http://localhost:9090

## � Initialisation de la Base de Données

L'initialisation de la base de données est **automatique** dans le pipeline, mais peut être exécutée manuellement :

### Initialisation Manuelle
```powershell
# Windows PowerShell
.\docker-sigeti.ps1 init-db

# Linux/macOS/WSL avec Make  
make init-db
```

### Test d'Initialisation
```powershell
# Windows PowerShell
.\docker-sigeti.ps1 test-init

# Linux/macOS/WSL avec Make
make test-init
```

> 📋 **Note** : L'initialisation est **idempotente** - elle peut être exécutée plusieurs fois sans problème. Elle crée uniquement les éléments manquants (base de données, utilisateur, schémas).

Pour plus de détails, consultez [DATABASE_INIT.md](DATABASE_INIT.md).

## 📊 Commandes de Test et Validation

### � **Choix de l'Interface**
Vous avez **deux options** pour gérer SIGETI DWH Docker :

- **🪟 Windows PowerShell** : `.\docker-sigeti.ps1 <command>` (recommandé Windows)
- **🐧 Make** : `make <command>` (Linux/macOS/WSL)

### �🎮 **Script PowerShell (Windows)**
```powershell
# Aide complète
.\docker-sigeti.ps1 help

# Démarrage complet
.\docker-sigeti.ps1 up

# Logs en temps réel
.\docker-sigeti.ps1 logs

# Status des services
.\docker-sigeti.ps1 status

# Nettoyage complet
.\docker-sigeti.ps1 clean
```

### 🔧 **Commandes Make (Linux/macOS/WSL)**
```bash
# Aide complète
make help

# Démarrage complet
make build
make up

# Logs en temps réel
make logs
make logs-airflow

# Status des services
make status

# Nettoyage complet
make clean
make clean-all
```

### 📊 **Table de Correspondance**
| Action | Windows PowerShell | Linux/macOS Make |
|--------|-------------------|------------------|
| Aide | `.\docker-sigeti.ps1 help` | `make help` |
| Construire | `.\docker-sigeti.ps1 build` | `make build` |
| Démarrer | `.\docker-sigeti.ps1 up` | `make up` |
| Arrêter | `.\docker-sigeti.ps1 down` | `make down` |
| Status | `.\docker-sigeti.ps1 status` | `make status` |
| Logs | `.\docker-sigeti.ps1 logs` | `make logs` |
| Test DB | `.\docker-sigeti.ps1 test-db` | `make test-db-connection` |
| Nettoyage | `.\docker-sigeti.ps1 clean` | `make clean` |
| Sauvegarde | `.\docker-sigeti.ps1 backup` | `make backup` |
| Informations | `.\docker-sigeti.ps1 info` | `make info` |

### 🔧 **Docker Compose Direct**
```powershell
# Démarrage sélectif
docker-compose up -d airflow-webserver airflow-scheduler

docker-compose up -d grafana prometheus

# Logs spécifiques
docker-compose logs -f airflow-webserver
docker-compose logs -f dbt-service

# Shell dans un conteneur
docker-compose exec airflow-webserver bash
docker-compose exec dbt-service bash
```

## 🎯 Tests et Validation

### ✅ **Test de Connectivité**
```powershell
# Windows PowerShell
.\docker-sigeti.ps1 test-db-connection
.\docker-sigeti.ps1 test-kpi
.\docker-sigeti.ps1 test-init
.\docker-sigeti.ps1 init-db
.\docker-sigeti.ps1 test-dbt
.\docker-sigeti.ps1 test-dbt-docker
.\docker-sigeti.ps1 run-etl
```

```bash
# Linux/macOS/WSL avec Make
make test-db-connection
make test-kpi
make test-init
make init-db
make test-dbt
make test-dbt-docker
make run-etl
```

### 🔍 **Validation des Services**
```powershell
# Vérification Airflow
curl http://localhost:8080/health


curl http://localhost:8888

# Test Grafana
curl http://localhost:3000/api/health
```

## 📊 Configuration Monitoring

### 📈 **Grafana Setup**
1. Accès : http://localhost:3000 (admin/admin123)
2. Datasources préconfigurées :
   - **Prometheus** : http://prometheus:9090
   - **SIGETI_DWH** : host.docker.internal:5432
3. Dashboards : `/monitoring/grafana/dashboards/`

### 📊 **Métriques Prometheus**
- **Airflow** : Métriques ETL et tâches
- **Système** : Via node-exporter (si installé)
- **PostgreSQL** : Via postgres-exporter (si configuré)

## 🔧 Développement

### 🛠️ **Mode Développement**
```powershell
# Windows PowerShell
.\docker-sigeti.ps1 dev

# Environnement de dev complet
docker-compose -f docker-compose.dev.yml up -d
```

```bash
# Linux/macOS/WSL avec Make
make dev

# Services individuels
make airflow-up

make monitoring-up
```

**Accès aux outils de dev** (mode dev complet) :
- Adminer: http://localhost:8082
- pgAdmin: http://localhost:8083  
- Redis Insight: http://localhost:8084

### 📝 **Hot Reload**
Les volumes sont montés pour le hot-reload :
- `./airflow/dags` → `/opt/airflow/dags`
- `./scripts` → `/opt/airflow/scripts`  
- `./sql_views` → `/opt/airflow/sql_views`
- `./dbt_sigeti` → `/opt/airflow/dbt_sigeti`

### 🧪 **Tests Unitaires**
```powershell
# Dans le conteneur dbt
docker-compose exec dbt-service pytest

# Dans le conteneur Airflow  
docker-compose exec airflow-webserver python -m pytest /opt/airflow/tests/
```

## 🗂️ Structure des Fichiers

```
SIGETI_DWH/
├── docker-compose.yml          # Configuration principale
├── docker-compose.dev.yml      # Configuration développement
├── docker-sigeti.ps1          # Script PowerShell de gestion
├── .env                       # Variables d'environnement
├── .dockerignore             # Fichiers ignorés par Docker
├── docker/                   # Dockerfiles spécialisés
│   ├── Dockerfile.airflow    # Image Airflow personnalisée
│   ├── Dockerfile.dbt        # Image dbt

│   ├── Dockerfile.dev        # Image développement
│   └── entrypoint-airflow.sh # Script d'initialisation Airflow
├── monitoring/               # Configuration monitoring
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/

│   └── analyse_kpi_sigeti.ipynb
└── scripts/                # Scripts copiés dans les conteneurs
    ├── create_kpi_views.py
    └── etl_sigeti.py
```

## 🔧 Troubleshooting

### ❌ **Problèmes Courants**

**1. Erreur de connexion DB**
```powershell
# Vérifier que les DBs locales sont actives
netstat -an | findstr :5432

# Tester depuis un conteneur
docker-compose exec airflow-webserver ping host.docker.internal
```

**2. Airflow ne démarre pas**
```powershell
# Réinitialiser Airflow
docker-compose down -v
.\docker-sigeti.ps1 init-airflow
.\docker-sigeti.ps1 up
```

**3. Volumes de données corrompus**
```powershell
# Nettoyage complet
.\docker-sigeti.ps1 clean-all
.\docker-sigeti.ps1 build
.\docker-sigeti.ps1 up
```

### 🩺 **Diagnostic**
```powershell
# Logs détaillés
docker-compose logs --tail=100 airflow-webserver

# Status des conteneurs
docker ps -a

# Utilisation des ressources
docker stats

# Inspection d'un service
docker-compose exec airflow-webserver env
```

## 💾 Sauvegarde et Restauration

### 💾 **Sauvegarde**
```powershell
# Windows PowerShell
.\docker-sigeti.ps1 backup
```

```bash
# Linux/macOS/WSL avec Make
make backup
```

```bash
# Sauvegarde manuelle volumes (toutes plateformes)
docker run --rm -v sigeti_dwh_airflow_postgres_data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/airflow_backup.tar.gz -C /data .
```

### 🔄 **Restauration**
```powershell
# Restaurer un volume
docker run --rm -v sigeti_dwh_airflow_postgres_data:/data -v ${PWD}/backups:/backup alpine tar xzf /backup/airflow_backup.tar.gz -C /data
```

## 🚀 Production

### 🏭 **Configuration Production**
- Modifier `.env` avec les vraies credentials
- Configurer SSL/TLS pour Grafana
- Mettre en place la sauvegarde automatique
- Configurer les alertes Prometheus
- Limiter les ressources Docker (`resources` dans compose)

### 📊 **Monitoring Production**
- Logs centralisés (ELK Stack ou equivalent)
- Métriques business dans Grafana  
- Alertes sur échecs ETL
- Monitoring santé des conteneurs

---

🎯 **Support** : Pour toute question, consulter les logs avec `.\docker-sigeti.ps1 logs` ou `docker-compose logs -f <service>`