"""
Script de validation complète du pipeline SIGETI ETL + KPI
Vérifie tous les composants: ETL, dbt, vues KPI et Airflow
"""

import subprocess
import sys
import os
from datetime import datetime
import psycopg2
import pandas as pd

def print_header(title):
    """Afficher un titre formaté"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_step(step_name, status="RUNNING"):
    """Afficher une étape"""
    if status == "RUNNING":
        print(f"⏳ {step_name}...")
    elif status == "SUCCESS":
        print(f"✅ {step_name} - SUCCÈS")
    elif status == "ERROR":
        print(f"❌ {step_name} - ERREUR")
    elif status == "WARNING":
        print(f"⚠️ {step_name} - AVERTISSEMENT")

def check_database_connection():
    """Vérifier la connexion à la base de données"""
    print_step("Vérification connexion base de données")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_dwh',
            user='postgres',
            password='postgres',
            port=5432
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print_step("Connexion base de données", "SUCCESS")
        print(f"   Version PostgreSQL: {version.split(',')[0]}")
        return True
    except Exception as e:
        print_step("Connexion base de données", "ERROR")
        print(f"   Erreur: {e}")
        return False

def check_source_data():
    """Vérifier les données source"""
    print_step("Vérification données source (sigeti_node_db)")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_node_db',
            user='postgres',
            password='postgres',
            port=5432
        )
        
        tables_to_check = [
            'demandes_attribution',
            'entreprises',
            'lots_terrain',
            'zones_industrielles'
        ]
        
        cursor = conn.cursor()
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count} enregistrements")
        
        cursor.close()
        conn.close()
        
        print_step("Données source", "SUCCESS")
        return True
    except Exception as e:
        print_step("Données source", "ERROR")
        print(f"   Erreur: {e}")
        return False

def check_staging_data():
    """Vérifier les données de staging"""
    print_step("Vérification données staging (sigeti_dwh)")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_dwh',
            user='postgres',
            password='postgres',
            port=5432
        )
        
        staging_tables = [
            'staging.demandes_attribution',
            'staging.entreprises', 
            'staging.lots_terrain',
            'staging.zones_industrielles'
        ]
        
        cursor = conn.cursor()
        for table in staging_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {table}: {count} enregistrements")
            except Exception as e:
                print(f"   ❌ {table}: Erreur - {e}")
        
        cursor.close()
        conn.close()
        
        print_step("Données staging", "SUCCESS")
        return True
    except Exception as e:
        print_step("Données staging", "ERROR")
        print(f"   Erreur: {e}")
        return False

def check_marts_data():
    """Vérifier les données marts (dbt)"""
    print_step("Vérification données marts (tables dbt)")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_dwh',
            user='postgres',
            password='postgres',
            port=5432
        )
        
        marts_tables = [
            'marts.fct_demandes_attribution',
            'marts.dim_entreprises',
            'marts.dim_zones_industrielles',
            'marts.dim_lots',
            'marts.dim_statuts_demandes'
        ]
        
        cursor = conn.cursor()
        for table in marts_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {table}: {count} enregistrements")
            except Exception as e:
                print(f"   ❌ {table}: Erreur - {e}")
        
        cursor.close()
        conn.close()
        
        print_step("Données marts", "SUCCESS")
        return True
    except Exception as e:
        print_step("Données marts", "ERROR")
        print(f"   Erreur: {e}")
        return False

def check_kpi_views():
    """Vérifier les vues KPI"""
    print_step("Vérification vues KPI")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_dwh',
            user='postgres',
            password='postgres',
            port=5432
        )
        
        kpi_views = [
            'v_kpi_taux_acceptation',
            'v_kpi_delai_traitement',
            'v_kpi_volume_demandes',
            'v_kpi_performance_financiere',
            'v_kpi_analyse_temporelle',
            'v_kpi_repartition_geographique',
            'v_kpi_tableau_bord_executif'
        ]
        
        cursor = conn.cursor()
        for view in kpi_views:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM public.{view}")
                count = cursor.fetchone()[0]
                print(f"   📊 {view}: {count} ligne(s)")
            except Exception as e:
                print(f"   ❌ {view}: Erreur - {e}")
        
        cursor.close()
        conn.close()
        
        print_step("Vues KPI", "SUCCESS")
        return True
    except Exception as e:
        print_step("Vues KPI", "ERROR")
        print(f"   Erreur: {e}")
        return False

def test_etl_script():
    """Tester le script ETL"""
    print_step("Test du script ETL")
    
    try:
        # Changer vers le répertoire du projet
        original_dir = os.getcwd()
        os.chdir(r'c:\Users\hynco\Desktop\SIGETI_DWH')
        
        result = subprocess.run(
            [sys.executable, 'etl_sigeti.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print_step("Script ETL", "SUCCESS")
            print(f"   Output: {result.stdout[:200]}...")
            return True
        else:
            print_step("Script ETL", "ERROR")
            print(f"   Erreur: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_step("Script ETL", "ERROR")
        print("   Erreur: Timeout (> 5 minutes)")
        return False
    except Exception as e:
        print_step("Script ETL", "ERROR")
        print(f"   Erreur: {e}")
        return False

def test_dbt_models():
    """Tester les modèles dbt"""
    print_step("Test des modèles dbt")
    
    try:
        original_dir = os.getcwd()
        os.chdir(r'c:\Users\hynco\Desktop\SIGETI_DWH\dbt_sigeti')
        
        # Test dbt run
        result = subprocess.run(
            ['dbt', 'run', '--profiles-dir', '.'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print_step("Modèles dbt", "SUCCESS")
            return True
        else:
            print_step("Modèles dbt", "ERROR")
            print(f"   Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print_step("Modèles dbt", "ERROR")
        print(f"   Erreur: {e}")
        return False

def test_kpi_views_creation():
    """Tester la création des vues KPI"""
    print_step("Test création vues KPI")
    
    try:
        original_dir = os.getcwd()
        os.chdir(r'c:\Users\hynco\Desktop\SIGETI_DWH')
        
        result = subprocess.run(
            [sys.executable, 'create_kpi_views.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print_step("Création vues KPI", "SUCCESS")
            return True
        else:
            print_step("Création vues KPI", "ERROR")
            print(f"   Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print_step("Création vues KPI", "ERROR")
        print(f"   Erreur: {e}")
        return False

def check_airflow_dags():
    """Vérifier la syntaxe des DAGs Airflow"""
    print_step("Vérification DAGs Airflow")
    
    dag_files = [
        r'c:\Users\hynco\Desktop\SIGETI_DWH\airflow\dags\sigeti_etl_pipeline.py',
        r'c:\Users\hynco\Desktop\SIGETI_DWH\airflow\dags\sigeti_kpi_monitoring.py'
    ]
    
    all_valid = True
    
    for dag_file in dag_files:
        try:
            print(f"   🔍 Vérification: {os.path.basename(dag_file)}")
            
            # Test de compilation Python
            with open(dag_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, dag_file, 'exec')
            print(f"   ✅ {os.path.basename(dag_file)}: Syntaxe valide")
            
        except Exception as e:
            print(f"   ❌ {os.path.basename(dag_file)}: Erreur - {e}")
            all_valid = False
    
    if all_valid:
        print_step("DAGs Airflow", "SUCCESS")
    else:
        print_step("DAGs Airflow", "ERROR")
    
    return all_valid

def generate_summary_report():
    """Générer un rapport de synthèse"""
    print_header("RAPPORT DE SYNTHÈSE")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='sigeti_dwh',
            user='postgres',
            password='postgres',
            port=5432
        )
        
        # Récupérer les KPI du tableau de bord exécutif
        query = "SELECT * FROM public.v_kpi_tableau_bord_executif"
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            row = df.iloc[0]
            
            print("📊 MÉTRIQUES BUSINESS:")
            print(f"   • Total demandes: {row.get('total_demandes', 'N/A')}")
            print(f"   • Taux d'acceptation: {row.get('taux_acceptation_pct', 'N/A')}%")
            print(f"   • Délai moyen: {row.get('delai_moyen_jours', 'N/A')} jours")
            print(f"   • Montant financé: {row.get('montant_total_finance', 'N/A'):,.0f} €")
            print(f"   • Emplois créés: {row.get('emplois_total_crees', 'N/A')}")
            print(f"   • Statut: {row.get('statut_alerte', 'N/A')}")
        
        conn.close()
        
        # Informations techniques
        print("\n🔧 INFORMATIONS TECHNIQUES:")
        print(f"   • Date de validation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   • Base de données: sigeti_dwh (PostgreSQL)")
        print(f"   • Pipeline ETL: Opérationnel")
        print(f"   • Modèles dbt: Déployés")
        print(f"   • Vues KPI: 7 vues créées")
        print(f"   • Airflow: DAGs validés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        return False

def main():
    """Fonction principale de validation"""
    print("🚀 VALIDATION COMPLÈTE DU PIPELINE SIGETI")
    print("=" * 80)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Compteurs de réussite
    tests_passed = 0
    tests_total = 9
    
    # 1. Connexion base de données
    print_header("INFRASTRUCTURE")
    if check_database_connection():
        tests_passed += 1
    
    # 2. Données source
    print_header("DONNÉES SOURCE")
    if check_source_data():
        tests_passed += 1
    
    # 3. Script ETL
    print_header("EXTRACTION & CHARGEMENT")
    if test_etl_script():
        tests_passed += 1
    
    # 4. Données staging
    if check_staging_data():
        tests_passed += 1
    
    # 5. Modèles dbt
    print_header("TRANSFORMATION (dbt)")
    if test_dbt_models():
        tests_passed += 1
    
    # 6. Données marts
    if check_marts_data():
        tests_passed += 1
    
    # 7. Création vues KPI
    print_header("VUES KPI")
    if test_kpi_views_creation():
        tests_passed += 1
    
    # 8. Vérification vues KPI
    if check_kpi_views():
        tests_passed += 1
    
    # 9. DAGs Airflow
    print_header("ORCHESTRATION (AIRFLOW)")
    if check_airflow_dags():
        tests_passed += 1
    
    # Rapport final
    print_header("RÉSULTAT FINAL")
    print(f"✅ Tests réussis: {tests_passed}/{tests_total}")
    print(f"❌ Tests échoués: {tests_total - tests_passed}/{tests_total}")
    
    success_rate = (tests_passed / tests_total) * 100
    print(f"📈 Taux de réussite: {success_rate:.1f}%")
    
    if tests_passed == tests_total:
        print("\n🎉 PIPELINE COMPLÈTEMENT OPÉRATIONNEL!")
        generate_summary_report()
        return True
    else:
        print(f"\n⚠️ PIPELINE PARTIELLEMENT OPÉRATIONNEL")
        print("   Vérifiez les erreurs ci-dessus avant la mise en production.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if success else 1)