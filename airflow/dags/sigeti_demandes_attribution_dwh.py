"""
DAG Airflow pour l'orchestration des transformations dbt
Modèle en étoile : Analyse des Demandes d'Attribution SIGETI

Ce DAG orchestre la création et mise à jour du modèle dimensionnel
pour l'analyse des demandes d'attribution de terrains.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.bash.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.email import EmailOperator

# Configuration par défaut du DAG
default_args = {
    'owner': 'sigeti-data-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Définition du DAG
dag = DAG(
    'sigeti_demandes_attribution_dwh',
    default_args=default_args,
    description='Pipeline DWH - Analyse des Demandes d\'Attribution',
    schedule_interval='0 6 * * *',  # Tous les jours à 6h00
    max_active_runs=1,
    tags=['sigeti', 'dwh', 'demandes-attribution', 'dbt']
)

# Task de début
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

# Vérification de la connectivité dbt
check_dbt = BashOperator(
    task_id='check_dbt_connection',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt debug --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Installation des dépendances dbt
install_dbt_deps = BashOperator(
    task_id='install_dbt_dependencies',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt deps --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Création de la dimension date (une seule fois)
build_dim_date = BashOperator(
    task_id='build_dim_date',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models dim_date --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Exécution des modèles de staging
run_staging_models = BashOperator(
    task_id='run_staging_models',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models tag:staging --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Construction des dimensions (en parallèle)
build_dim_entreprises = BashOperator(
    task_id='build_dim_entreprises',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models dim_entreprises --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

build_dim_zones = BashOperator(
    task_id='build_dim_zones_industrielles',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models dim_zones_industrielles --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

build_dim_lots = BashOperator(
    task_id='build_dim_lots',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models dim_lots --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

build_dim_statuts = BashOperator(
    task_id='build_dim_statuts_demandes',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models dim_statuts_demandes --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Construction de la table de faits (après toutes les dimensions)
build_fact_table = BashOperator(
    task_id='build_fct_demandes_attribution',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt run --models fct_demandes_attribution --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Exécution des tests dbt
run_dbt_tests = BashOperator(
    task_id='run_dbt_tests',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt test --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Génération de la documentation dbt
generate_docs = BashOperator(
    task_id='generate_dbt_docs',
    bash_command='''
    cd /opt/dbt/sigeti_dwh
    dbt docs generate --profiles-dir /opt/dbt/profiles
    ''',
    dag=dag
)

# Mise à jour des statistiques PostgreSQL
update_statistics = PostgresOperator(
    task_id='update_table_statistics',
    postgres_conn_id='sigeti_dwh_postgres',
    sql='''
    -- Mise à jour des statistiques pour optimiser les requêtes
    ANALYZE marts.dim_entreprises;
    ANALYZE marts.dim_zones_industrielles;
    ANALYZE marts.dim_lots;
    ANALYZE marts.dim_statuts_demandes;
    ANALYZE marts.dim_date;
    ANALYZE marts.fct_demandes_attribution;
    
    -- Création d'index si nécessaire
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fct_demandes_date_creation 
        ON marts.fct_demandes_attribution (date_creation_key);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fct_demandes_zone 
        ON marts.fct_demandes_attribution (zone_key);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fct_demandes_statut 
        ON marts.fct_demandes_attribution (statut_key);
    ''',
    dag=dag
)

# Task de fin réussie
success_task = DummyOperator(
    task_id='pipeline_success',
    dag=dag
)

# Email de notification en cas de succès
send_success_email = EmailOperator(
    task_id='send_success_notification',
    to=['data-team@sigeti.com'],
    subject='✅ Pipeline DWH Demandes Attribution - Succès',
    html_content='''
    <h3>Pipeline DWH - Demandes d'Attribution</h3>
    <p>Le pipeline de transformation des données s'est exécuté avec succès.</p>
    <p><strong>Date d'exécution:</strong> {{ ds }}</p>
    <p><strong>Durée:</strong> {{ macros.timedelta(ti.end_date - ti.start_date) }}</p>
    <p>Les indicateurs de gestion des demandes d'attribution sont maintenant à jour.</p>
    ''',
    dag=dag,
    trigger_rule='all_success'
)

# Définition des dépendances
start_task >> check_dbt >> install_dbt_deps

install_dbt_deps >> build_dim_date
install_dbt_deps >> run_staging_models

run_staging_models >> [
    build_dim_entreprises,
    build_dim_zones,
    build_dim_lots,
    build_dim_statuts
]

[build_dim_date, build_dim_entreprises, build_dim_zones, 
 build_dim_lots, build_dim_statuts] >> build_fact_table

build_fact_table >> run_dbt_tests >> generate_docs >> update_statistics

update_statistics >> success_task >> send_success_email