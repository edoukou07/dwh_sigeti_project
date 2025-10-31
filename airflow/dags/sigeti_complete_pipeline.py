#!/usr/bin/env python3
"""
DAG Airflow pour le pipeline ETL des Collectes, Recouvrements et Indicateurs Financiers SIGETI
Orchestration de l'extraction, transformation et création des KPI complets
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin des scripts
sys.path.append('/opt/airflow/scripts')

# Configuration du DAG
default_args = {
    'owner': 'sigeti-admin',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Création du DAG
dag = DAG(
    'sigeti_collectes_recouvrement_financial_pipeline',
    default_args=default_args,
    description='Pipeline ETL complet pour Collectes, Recouvrements et Indicateurs Financiers SIGETI',
    schedule_interval='0 6 * * *',  # Tous les jours à 6h00
    max_active_runs=1,
    tags=['sigeti', 'collectes', 'recouvrement', 'kpi', 'finance', 'paiements']
)

def run_etl_collectes():
    """Exécuter l'ETL des collectes et recouvrements"""
    try:
        from etl_collectes_pandas import ETLCollectesRecouvrements
        
        etl = ETLCollectesRecouvrements()
        success = etl.run_etl()
        
        if not success:
            raise Exception("ETL des collectes et recouvrements échoué")
        
        print("✅ ETL collectes terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur ETL collectes: {e}")
        raise

def run_etl_financial_to_dimensional():
    """Exécuter l'ETL financier vers le modèle dimensionnel"""
    try:
        import sys
        sys.path.append('/opt/airflow/scripts')
        
        # Importer et exécuter l'ETL financier
        exec(open('/opt/airflow/scripts/etl_financial_to_dimensional.py').read())
        
        print("✅ ETL financier vers dimensionnel terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur ETL financier dimensionnel: {e}")
        raise

def create_kpi_views():
    """Créer les vues KPI des collectes"""
    try:
        from create_kpi_collectes_views import deploy_kpi_views, test_kpi_views
        
        # Déployer les vues KPI
        if not deploy_kpi_views():
            raise Exception("Échec du déploiement des vues KPI collectes")
        
        # Tester les vues
        if not test_kpi_views():
            raise Exception("Échec des tests des vues KPI collectes")
        
        print("✅ Vues KPI collectes créées et testées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création KPI collectes: {e}")
        raise

def create_financial_kpi_views():
    """Créer les vues KPI financiers"""
    try:
        import psycopg2
        import os
        
        # Configuration de la base
        db_config = {
            'host': os.getenv('DWH_DB_HOST', 'localhost'),
            'port': os.getenv('DWH_DB_PORT', 5432),
            'database': os.getenv('DWH_DB_NAME', 'sigeti_dwh'),
            'user': os.getenv('DWH_DB_USER', 'sigeti_user'),
            'password': os.getenv('DWH_DB_PASSWORD', 'sigeti123')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Liste des vues KPI à créer
        kpi_financial_views = [
            '''CREATE OR REPLACE VIEW v_kpi_montant_total_paiements AS
            SELECT 'Montant Total des Paiements Reçus' as indicateur,
                   SUM(montant_paiement) as valeur,
                   'FCFA' as unite,
                   COUNT(*) as nombre_transactions,
                   CURRENT_DATE as date_calcul
            FROM fct_paiements WHERE montant_paiement > 0''',
            
            '''CREATE OR REPLACE VIEW v_kpi_revenus_paiements_reussis AS
            SELECT 'Revenus Totaux des Paiements Réussis' as indicateur,
                   SUM(montant_net) as valeur,
                   'FCFA' as unite,
                   COUNT(*) as nombre_paiements_reussis,
                   ROUND(AVG(montant_net), 2) as montant_moyen,
                   CURRENT_DATE as date_calcul
            FROM fct_paiements 
            WHERE statut_paiement_key IN ('PAYE_COMPLET', 'PAYE_PARTIEL', 'RECOUVRE')''',
            
            '''CREATE OR REPLACE VIEW v_dashboard_financier_complet AS
            SELECT 1 as ordre, '1. Montant Total Paiements' as kpi,
                   CONCAT(ROUND(valeur/1000000, 1), 'M FCFA') as valeur,
                   CONCAT(nombre_transactions, ' transactions') as detail
            FROM v_kpi_montant_total_paiements
            UNION ALL
            SELECT 2 as ordre, '2. Revenus Nets Réussis' as kpi,
                   CONCAT(ROUND(valeur/1000000, 1), 'M FCFA') as valeur,
                   CONCAT(nombre_paiements_reussis, ' paiements') as detail
            FROM v_kpi_revenus_paiements_reussis
            ORDER BY ordre'''
        ]
        
        # Exécuter chaque vue
        for view_sql in kpi_financial_views:
            cursor.execute(view_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Vues KPI financiers créées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création KPI financiers: {e}")
        raise

def validate_collectes_data():
    """Valider les données de collectes chargées"""
    try:
        import psycopg2
        import os
        
        # Configuration de la base
        db_config = {
            'host': os.getenv('DWH_DB_HOST', 'localhost'),
            'port': os.getenv('DWH_DB_PORT', 5432),
            'database': os.getenv('DWH_DB_NAME', 'sigeti_dwh'),
            'user': os.getenv('DWH_DB_USER', 'sigeti_user'),
            'password': os.getenv('DWH_DB_PASSWORD', 'sigeti123')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        validations = []
        
        # Validation 1: Vérifier les données de collectes
        cursor.execute("SELECT COUNT(*) FROM fct_collectes")
        count_collectes = cursor.fetchone()[0]
        validations.append(f"✅ Collectes: {count_collectes} enregistrements")
        
        # Validation 2: Vérifier les données de paiements
        cursor.execute("SELECT COUNT(*) FROM fct_paiements")
        count_paiements = cursor.fetchone()[0]
        validations.append(f"✅ Paiements: {count_paiements} enregistrements")
        
        # Validation 3: Vérifier les vues KPI
        cursor.execute("SELECT COUNT(*) FROM v_dashboard_financier_complet")
        count_kpi = cursor.fetchone()[0]
        validations.append(f"✅ KPI Financiers: {count_kpi} indicateurs")
        
        cursor.close()
        conn.close()
        
        for validation in validations:
            print(validation)
        
        print("✅ Validation des données réussie")
        return True
        
    except Exception as e:
        print(f"❌ Erreur validation données: {e}")
        raise

def generate_complete_report():
    """Générer le rapport complet collectes et financier"""
    try:
        import psycopg2
        import os
        from datetime import datetime
        
        # Configuration de la base
        db_config = {
            'host': os.getenv('DWH_DB_HOST', 'localhost'),
            'port': os.getenv('DWH_DB_PORT', 5432),
            'database': os.getenv('DWH_DB_NAME', 'sigeti_dwh'),
            'user': os.getenv('DWH_DB_USER', 'sigeti_user'),
            'password': os.getenv('DWH_DB_PASSWORD', 'sigeti123')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Générer le rapport financier
        cursor.execute("SELECT kpi, valeur, detail FROM v_dashboard_financier_complet ORDER BY ordre")
        rapport_financier = cursor.fetchall()
        
        # Créer le rapport complet
        rapport_contenu = f"""# RAPPORT COLLECTES, RECOUVREMENTS ET INDICATEURS FINANCIERS SIGETI
## Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 💰 INDICATEURS FINANCIERS ET DE PAIEMENT

"""
        
        # Ajouter les KPI financiers
        if rapport_financier:
            for kpi in rapport_financier:
                rapport_contenu += f"""### {kpi[0]}
- **Valeur**: {kpi[1]}
- **Détail**: {kpi[2]}

"""
        
        rapport_contenu += """
## 📊 RÉSUMÉ TECHNIQUE
- Architecture: PostgreSQL Dimensionnelle
- Pipeline ETL: Airflow
- KPI: Temps réel via vues matérialisées
- Fréquence: Quotidienne à 6h00

---
*Rapport généré automatiquement par le pipeline SIGETI ETL*
"""
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rapport_path = f'/opt/airflow/reports/rapport_sigeti_complet_{timestamp}.md'
        
        os.makedirs('/opt/airflow/reports', exist_ok=True)
        with open(rapport_path, 'w', encoding='utf-8') as f:
            f.write(rapport_contenu)
        
        print(f"✅ Rapport sauvegardé: {rapport_path}")
        print(rapport_contenu)
        
        cursor.close()
        conn.close()
        
        print("✅ Génération rapport terminée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        raise

# Définition des tâches

# Tâche de début
start_task = DummyOperator(
    task_id='start_sigeti_complete_pipeline',
    dag=dag
)

# ETL des collectes et recouvrements
etl_collectes_task = PythonOperator(
    task_id='etl_collectes_recouvrements',
    python_callable=run_etl_collectes,
    dag=dag
)

# ETL financier vers dimensionnel
etl_financial_task = PythonOperator(
    task_id='etl_financial_to_dimensional',
    python_callable=run_etl_financial_to_dimensional,
    dag=dag
)

# Exécution des modèles dbt (modèles staging)
dbt_staging_task = BashOperator(
    task_id='dbt_run_staging_collectes',
    bash_command="""
    cd /opt/airflow/dbt_sigeti && 
    dbt run --models staging.stg_collectes staging.stg_agents_collecteurs staging.stg_recouvrements
    """,
    dag=dag
)

# Exécution des modèles dbt (dimensions et faits)
dbt_marts_task = BashOperator(
    task_id='dbt_run_marts_collectes',
    bash_command="""
    cd /opt/airflow/dbt_sigeti && 
    dbt run --models marts.dim_agents_collecteurs marts.fct_collectes_recouvrements
    """,
    dag=dag
)

# Création des vues KPI collectes
kpi_views_task = PythonOperator(
    task_id='create_collectes_kpi_views',
    python_callable=create_kpi_views,
    dag=dag
)

# Création des vues KPI financiers
financial_kpi_views_task = PythonOperator(
    task_id='create_financial_kpi_views',
    python_callable=create_financial_kpi_views,
    dag=dag
)

# Tests dbt
dbt_test_task = BashOperator(
    task_id='dbt_test_collectes',
    bash_command="""
    cd /opt/airflow/dbt_sigeti && 
    dbt test --models staging.stg_collectes staging.stg_agents_collecteurs marts.dim_agents_collecteurs marts.fct_collectes_recouvrements
    """,
    dag=dag,
    trigger_rule='none_failed'
)

# Validation des données
validation_task = PythonOperator(
    task_id='validate_complete_data',
    python_callable=validate_collectes_data,
    dag=dag
)

# Génération du rapport complet
report_task = PythonOperator(
    task_id='generate_complete_report',
    python_callable=generate_complete_report,
    dag=dag
)

# Tâche de fin
end_task = DummyOperator(
    task_id='end_sigeti_complete_pipeline',
    dag=dag
)

# Définition des dépendances du pipeline complet
start_task >> etl_collectes_task
etl_collectes_task >> [dbt_staging_task, etl_financial_task]
dbt_staging_task >> dbt_marts_task
dbt_marts_task >> kpi_views_task
etl_financial_task >> financial_kpi_views_task

# Correction: connecter les tâches individuellement
kpi_views_task >> [dbt_test_task, validation_task]
financial_kpi_views_task >> [dbt_test_task, validation_task]

[dbt_test_task, validation_task] >> report_task
report_task >> end_task