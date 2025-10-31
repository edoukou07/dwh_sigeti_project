from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
import sys
import os

# Ajouter le répertoire scripts au path pour les imports
sys.path.append('/opt/airflow/scripts')

# Configuration du DAG
default_args = {
    'owner': 'sigeti-admin',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'sigeti_pipeline_simplified',
    default_args=default_args,
    description='Pipeline SIGETI simplifié (sans dbt)',
    schedule_interval='0 6 * * *',  # Tous les jours à 6h
    catchup=False,
    tags=['sigeti', 'etl', 'kpi', 'simplifié']
)

# Fonctions du pipeline (importées depuis le DAG principal)
def run_etl_collectes():
    """ETL des collectes et recouvrements"""
    try:
        from etl_collectes_pandas import ETLCollectesRecouvrements
        
        etl = ETLCollectesRecouvrements()
        success = etl.run_etl()
        
        if not success:
            raise Exception("ETL des collectes et recouvrements échoué")
        
        print("✅ ETL collectes et recouvrements terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur ETL collectes: {e}")
        raise Exception("ETL des collectes et recouvrements échoué")

def run_etl_financial():
    """ETL financier vers modèle dimensionnel"""
    try:
        from etl_financial_to_dimensional import extract_transform_load
        
        success = extract_transform_load()
        
        if not success:
            raise Exception("ETL financier dimensionnel échoué")
        
        print("✅ ETL financier dimensionnel terminé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur ETL financier dimensionnel: {e}")
        raise

def create_financial_kpi_views():
    """Créer les vues KPI financiers"""
    try:
        import psycopg2
        import os
        
        # Configuration de la connexion
        config = {
            'host': os.getenv('DWH_DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
            'port': int(os.getenv('DWH_DB_PORT', os.getenv('POSTGRES_PORT', 5432))),
            'database': os.getenv('DWH_DB_NAME', os.getenv('POSTGRES_DB', 'sigeti_dwh')),
            'user': os.getenv('DWH_DB_USER', os.getenv('POSTGRES_USER', 'sigeti_user')),
            'password': os.getenv('DWH_DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'sigeti123'))
        }
        
        # Connexion à la base de données
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Vue 1: Collectes par période
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_collectes_periode AS
        SELECT 
            date_trunc('month', date_creation) as periode,
            COUNT(*) as nombre_collectes,
            SUM(montant_paiement) as montant_total,
            AVG(montant_paiement) as montant_moyen
        FROM fct_paiements
        WHERE type_transaction = 'COLLECTE'
        GROUP BY date_trunc('month', date_creation)
        ORDER BY periode DESC
        """)
        
        # Vue 2: Performance des agents
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_agents_performance AS
        SELECT 
            agent_id,
            COUNT(*) as nombre_operations,
            SUM(montant_paiement) as montant_collecte,
            COUNT(CASE WHEN est_paiement_complet THEN 1 END) as paiements_complets,
            ROUND(
                COUNT(CASE WHEN est_paiement_complet THEN 1 END) * 100.0 / COUNT(*), 2
            ) as taux_reussite_pct
        FROM fct_paiements 
        WHERE agent_id IS NOT NULL
        GROUP BY agent_id
        ORDER BY montant_collecte DESC
        """)
        
        # Vue 3: Recouvrement par zone
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_recouvrement_zone AS
        SELECT 
            zone_key,
            COUNT(*) as nombre_recouvrements,
            SUM(montant_paiement) as montant_recouvre,
            COUNT(CASE WHEN est_en_retard THEN 1 END) as retards,
            ROUND(
                COUNT(CASE WHEN est_en_retard THEN 1 END) * 100.0 / COUNT(*), 2
            ) as taux_retard_pct
        FROM fct_paiements
        WHERE type_transaction = 'RECOUVREMENT'
        GROUP BY zone_key
        ORDER BY montant_recouvre DESC
        """)
        
        # Vue 4: Évolution mensuelle
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_evolution_mensuelle AS
        SELECT 
            date_trunc('month', date_creation) as mois,
            type_transaction,
            COUNT(*) as nombre_operations,
            SUM(montant_paiement) as montant_total
        FROM fct_paiements
        GROUP BY date_trunc('month', date_creation), type_transaction
        ORDER BY mois DESC, type_transaction
        """)
        
        # Vue 5: Méthodes de paiement
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_methodes_paiement AS
        SELECT 
            methode_paiement_key,
            COUNT(*) as nombre_transactions,
            SUM(montant_paiement) as montant_total,
            ROUND(AVG(montant_paiement), 2) as montant_moyen
        FROM fct_paiements
        GROUP BY methode_paiement_key
        ORDER BY montant_total DESC
        """)
        
        # Vue 6: Tableau de bord global
        cursor.execute("""
        CREATE OR REPLACE VIEW vw_kpi_dashboard_global AS
        SELECT 
            'GLOBAL' as indicateur,
            COUNT(*) as total_transactions,
            SUM(montant_paiement) as montant_global,
            COUNT(CASE WHEN type_transaction = 'COLLECTE' THEN 1 END) as collectes,
            COUNT(CASE WHEN type_transaction = 'RECOUVREMENT' THEN 1 END) as recouvrements,
            COUNT(CASE WHEN est_paiement_complet THEN 1 END) as paiements_complets,
            COUNT(CASE WHEN est_en_retard THEN 1 END) as paiements_retard,
            ROUND(
                COUNT(CASE WHEN est_paiement_complet THEN 1 END) * 100.0 / COUNT(*), 2
            ) as taux_reussite_global
        FROM fct_paiements
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ 6 vues KPI financiers créées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création vues KPI financiers: {e}")
        raise

# Définition des tâches
start_task = DummyOperator(
    task_id='start_sigeti_simplified_pipeline',
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
    task_id='etl_financial_kpis',
    python_callable=run_etl_financial,
    dag=dag
)

# Création des vues KPI financiers
financial_kpi_views_task = PythonOperator(
    task_id='create_financial_kpi_views',
    python_callable=create_financial_kpi_views,
    dag=dag
)

# Tâche de fin
end_task = DummyOperator(
    task_id='end_sigeti_simplified_pipeline',
    dag=dag
)

# Définition des dépendances (pipeline simplifié)
start_task >> etl_collectes_task >> etl_financial_task >> financial_kpi_views_task >> end_task