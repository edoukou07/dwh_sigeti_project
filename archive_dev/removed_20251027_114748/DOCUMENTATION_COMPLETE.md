# SIGETI Data Warehouse - Documentation Complète

## 🏗️ Architecture Globale

Le projet SIGETI Data Warehouse est une solution complète d'entrepôt de données pour la gestion et l'analyse des demandes d'attribution de terrains industriels en Tunisie.

### 🎯 Objectifs
- Centraliser les données des demandes d'attribution
- Automatiser les processus ETL
- Fournir des indicateurs de performance (KPI)
- Permettre l'analyse décisionnelle

### 📊 Indicateurs Clés (KPI)
1. **Taux d'acceptation** des demandes
2. **Délai de traitement** moyen
3. **Volume des demandes** par période
4. **Performance financière** et emploi
5. **Analyse temporelle** des tendances
6. **Répartition géographique** par zone
7. **Tableau de bord exécutif** consolidé

## 🏛️ Architecture Technique

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   sigeti_node_db│    │   SIGETI ETL     │    │   sigeti_dwh    │
│   (Source)      │───▶│   Pipeline       │───▶│   (Target)      │
│                 │    │                  │    │                 │
│ • demandes      │    │ • Python Script  │    │ • staging       │
│ • entreprises   │    │ • Data Cleaning  │    │ • marts         │
│ • lots_terrain  │    │ • UTF-8 Encoding │    │ • KPI Views     │
│ • zones_indus   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         │              │   dbt Project    │              │
         │              │                  │              │
         └──────────────│ • Transformations│──────────────┘
                        │ • Star Schema    │
                        │ • Data Quality   │
                        │ • Documentation  │
                        └──────────────────┘
                                 │
                     ┌──────────────────────┐
                     │   Apache Airflow     │
                     │                      │
                     │ • Pipeline Scheduler │
                     │ • KPI Monitoring     │
                     │ • Error Handling     │
                     │ • Notifications      │
                     └──────────────────────┘
```

## 📁 Structure du Projet

```
SIGETI_DWH/
├── 📁 airflow/                    # Orchestration Apache Airflow
│   ├── 📁 dags/                  # Définitions des DAGs
│   │   ├── sigeti_etl_pipeline.py          # Pipeline ETL principal
│   │   └── sigeti_kpi_monitoring.py        # Monitoring KPI
│   ├── 📁 logs/                  # Logs d'exécution
│   ├── 📁 plugins/               # Plugins personnalisés
│   ├── airflow.cfg               # Configuration Airflow
│   ├── requirements.txt          # Dépendances Python
│   ├── setup_airflow.py         # Script d'installation
│   ├── start_scheduler.bat      # Démarrage scheduler (Windows)
│   ├── start_webserver.bat      # Démarrage serveur web (Windows)
│   └── README.md                 # Documentation Airflow
│
├── 📁 dbt_sigeti/                # Projet dbt
│   ├── 📁 models/               # Modèles de données
│   │   ├── 📁 staging/          # Tables de staging
│   │   └── 📁 marts/           # Tables finales (star schema)
│   │       └── 📁 core/        # Fait et dimensions
│   ├── 📁 tests/               # Tests de qualité
│   ├── 📁 macros/              # Macros dbt
│   ├── dbt_project.yml         # Configuration projet
│   ├── profiles.yml            # Configuration connexions
│   └── packages.yml            # Packages dbt
│
├── 📁 sql_views/                 # Vues KPI SQL
│   ├── 01_v_kpi_taux_acceptation.sql      # Taux d'acceptation
│   ├── 02_v_kpi_delai_traitement.sql      # Délais de traitement
│   ├── 03_v_kpi_volume_demandes.sql       # Volume des demandes
│   ├── 04_v_kpi_performance_financiere.sql # Performance financière
│   ├── 05_v_kpi_analyse_temporelle.sql    # Analyse temporelle
│   ├── 06_v_kpi_repartition_geographique.sql # Répartition géo
│   ├── 07_v_kpi_tableau_bord_executif.sql # Tableau de bord
│   ├── deploy_views.sql                   # Script de déploiement
│   └── README.md                          # Documentation vues
│
├── 📄 etl_sigeti.py              # Script ETL principal (Python/Pandas)
├── 📄 etl_sigeti_spark.py        # Script ETL PySpark (alternatif)
├── 📄 create_kpi_views.py        # Création automatique des vues
├── 📄 test_kpi_views.py          # Tests et validation des vues
├── 📄 validate_pipeline.py       # Validation complète du pipeline
├── 📄 kpi_manager.bat            # Gestionnaire vues KPI (Windows)
└── 📄 README.md                  # Documentation principale
```

## 🚀 Déploiement et Installation

### Prérequis
- Python 3.8+
- PostgreSQL 12+
- dbt-core 1.7+
- Apache Airflow 2.8+

### Installation pas à pas

#### 1. Base de données
```sql
-- Créer les bases de données
CREATE DATABASE sigeti_node_db;  -- Base source
CREATE DATABASE sigeti_dwh;      -- Entrepôt de données
```

#### 2. Environnement Python
```bash
cd c:\Users\hynco\Desktop\SIGETI_DWH
pip install -r requirements.txt
```

#### 3. Configuration dbt
```bash
cd dbt_sigeti
dbt deps --profiles-dir .
dbt debug --profiles-dir .
```

#### 4. Installation Airflow
```bash
cd airflow
python setup_airflow.py
```

#### 5. Déploiement initial
```bash
# ETL initial
python etl_sigeti.py

# Transformations dbt
cd dbt_sigeti
dbt run --profiles-dir .

# Création des vues KPI
cd ..
python create_kpi_views.py
```

## 🔄 Utilisation Quotidienne

### Pipeline Automatique (Airflow)
```bash
# Démarrer Airflow
cd airflow
start_scheduler.bat    # Terminal 1
start_webserver.bat    # Terminal 2

# Interface web: http://localhost:8080
# Login: admin / admin123
```

### Exécution Manuelle
```bash
# Pipeline complet
python validate_pipeline.py

# ETL seul
python etl_sigeti.py

# Vues KPI seules
python create_kpi_views.py

# Tests
python test_kpi_views.py --summary
```

### Gestion des KPI
```bash
# Interface interactive
kpi_manager.bat

# Commandes directes
kpi_manager.bat deploy   # Déployer les vues
kpi_manager.bat test     # Tester les vues
kpi_manager.bat summary  # Résumé exécutif
```

## 📊 Modèle de Données

### Star Schema
- **Fait**: `fct_demandes_attribution` (table centrale)
- **Dimensions**:
  - `dim_entreprises` (entreprises)
  - `dim_zones_industrielles` (zones)
  - `dim_lots` (lots de terrain)
  - `dim_statuts_demandes` (statuts)
  - `dim_date` (dates)

### Métriques Principales
- Nombre de demandes
- Taux d'acceptation
- Délais de traitement
- Montants financés
- Emplois créés

## 🔍 Monitoring et Alertes

### Seuils d'Alerte
- **Taux d'acceptation**: < 30% = Alerte
- **Délai moyen**: > 15 jours = Alerte
- **Volume**: Variations importantes = Avertissement

### Notifications
- Email automatique en cas d'erreur
- Rapports quotidiens générés
- Tableau de bord temps réel

## 🛠️ Maintenance

### Tâches Régulières
- **Quotidien**: Vérification des logs, validation des KPI
- **Hebdomadaire**: Analyse des tendances, optimisation
- **Mensuel**: Révision des seuils, mise à jour documentation

### Troubleshooting
```bash
# Diagnostics
python validate_pipeline.py     # Validation complète
dbt test --profiles-dir .       # Tests de qualité
python test_kpi_views.py --test # Tests des vues

# Logs
tail -f airflow/logs/scheduler/latest/*.log
tail -f airflow/logs/dag_id/task_id/*/1.log
```

## 📈 Performances

### Métriques Actuelles
- **Volume de données**: ~77 enregistrements
- **Temps d'exécution ETL**: ~30 secondes
- **Temps dbt**: ~15 secondes
- **Temps total pipeline**: ~2 minutes

### Optimisations
- Index sur les clés étrangères
- Partitionnement par date si volume important
- Mise en cache des vues fréquemment utilisées

## 🔐 Sécurité

### Accès aux Données
- Authentification PostgreSQL requise
- Connexions chiffrées
- Audit des accès via logs

### Sauvegarde
- Backup automatique PostgreSQL
- Versioning du code (Git recommandé)
- Documentation des changements

## 🎯 Roadmap Future

### Améliorations Prévues
1. **Dashboards interactifs** (Power BI/Grafana)
2. **API REST** pour l'accès aux données
3. **Alertes intelligentes** avec ML
4. **Historisation** des changements
5. **Intégration** avec d'autres systèmes

### Évolutions Techniques
- Migration vers Apache Spark pour gros volumes
- Implémentation de Delta Lake
- CI/CD pour dbt et Airflow
- Containerisation avec Docker

## 📞 Support

### Documentation
- README principal: `/README.md`
- Documentation Airflow: `/airflow/README.md`
- Documentation vues KPI: `/sql_views/README.md`

### Validation
```bash
python validate_pipeline.py  # Test complet
```

### Contacts
- **Équipe technique**: [Votre équipe]
- **Business owner**: [Responsable métier]
- **Support IT**: [Support informatique]

---

**Version**: 1.0  
**Dernière mise à jour**: 27 octobre 2025  
**Status**: Production Ready ✅