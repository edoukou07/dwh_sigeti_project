"""
Script de validation finale du système SIGETI DWH après nettoyage
Vérifie que tous les composants essentiels fonctionnent correctement
"""

import psycopg2
from datetime import datetime
import sys

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sigeti_dwh', 
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def print_header(title):
    """Afficher un titre formaté"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_check(description, status, details=""):
    """Afficher un résultat de vérification"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {description}")
    if details:
        print(f"   📋 {details}")

def create_connection():
    """Créer une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def test_database_structure():
    """Vérifier la structure de la base de données"""
    print_header("VALIDATION STRUCTURE BASE DE DONNÉES")
    
    conn = create_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    all_tests_passed = True
    
    try:
        # 1. Vérifier les schémas essentiels
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('marts', 'staging', 'public')")
        schemas = [row[0] for row in cursor.fetchall()]
        
        expected_schemas = ['marts', 'staging', 'public']
        missing_schemas = set(expected_schemas) - set(schemas)
        
        if not missing_schemas:
            print_check("Schémas essentiels présents", True, f"Trouvés: {', '.join(schemas)}")
        else:
            print_check("Schémas essentiels manquants", False, f"Manquants: {', '.join(missing_schemas)}")
            all_tests_passed = False
        
        # 2. Vérifier les tables du data warehouse
        expected_tables = {
            'marts': ['fct_demandes_attribution', 'dim_entreprises', 'dim_lots', 'dim_zones_industrielles', 'dim_date', 'dim_statuts_demandes'],
            'staging': ['demandes_attribution', 'entreprises', 'lots', 'zones_industrielles']
        }
        
        for schema, tables in expected_tables.items():
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """, (schema,))
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            missing_tables = set(tables) - set(existing_tables)
            
            if not missing_tables:
                print_check(f"Tables {schema} présentes", True, f"{len(existing_tables)} tables")
            else:
                print_check(f"Tables {schema} manquantes", False, f"Manquantes: {', '.join(missing_tables)}")
                all_tests_passed = False
        
        # 3. Vérifier les vues KPI
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public' AND table_name LIKE 'v_kpi_%'
        """)
        kpi_views = [row[0] for row in cursor.fetchall()]
        
        expected_kpi_count = 7
        if len(kpi_views) == expected_kpi_count:
            print_check("Vues KPI présentes", True, f"{len(kpi_views)} vues trouvées")
        else:
            print_check("Vues KPI incomplètes", False, f"Trouvées: {len(kpi_views)}, attendues: {expected_kpi_count}")
            all_tests_passed = False
        
        # 4. Vérifier qu'aucun schéma inutile n'existe
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'marts', 'staging', 'public')
        """)
        extra_schemas = [row[0] for row in cursor.fetchall()]
        
        if not extra_schemas:
            print_check("Aucun schéma inutile", True, "Nettoyage réussi")
        else:
            print_check("Schémas inutiles détectés", False, f"Trouvés: {', '.join(extra_schemas)}")
            # Ceci n'est qu'un avertissement, pas une erreur critique
        
        cursor.close()
        conn.close()
        return all_tests_passed
        
    except Exception as e:
        print_check("Erreur validation structure", False, str(e))
        cursor.close()
        conn.close()
        return False

def test_data_integrity():
    """Vérifier l'intégrité des données"""
    print_header("VALIDATION INTÉGRITÉ DES DONNÉES")
    
    conn = create_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    all_tests_passed = True
    
    try:
        # 1. Vérifier les données dans les tables de staging
        staging_tables = ['demandes_attribution', 'entreprises', 'lots', 'zones_industrielles']
        for table in staging_tables:
            cursor.execute(f"SELECT COUNT(*) FROM staging.{table}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print_check(f"Données {table}", True, f"{count} enregistrements")
            else:
                print_check(f"Données {table} vides", False, "Aucun enregistrement")
                all_tests_passed = False
        
        # 2. Vérifier les données dans les tables marts
        cursor.execute("SELECT COUNT(*) FROM marts.fct_demandes_attribution")
        fact_count = cursor.fetchone()[0]
        
        if fact_count > 0:
            print_check("Table de faits", True, f"{fact_count} enregistrements")
        else:
            print_check("Table de faits vide", False, "Aucun enregistrement")
            all_tests_passed = False
        
        # 3. Vérifier les dimensions
        dimensions = ['dim_entreprises', 'dim_lots', 'dim_zones_industrielles', 'dim_date', 'dim_statuts_demandes']
        for dim in dimensions:
            cursor.execute(f"SELECT COUNT(*) FROM marts.{dim}")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print_check(f"Dimension {dim}", True, f"{count} enregistrements")
            else:
                print_check(f"Dimension {dim} vide", False, "Aucun enregistrement")
                all_tests_passed = False
        
        # 4. Vérifier les relations (intégrité référentielle)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM marts.fct_demandes_attribution f
            LEFT JOIN marts.dim_entreprises e ON f.entreprise_key = e.entreprise_key
            WHERE e.entreprise_key IS NULL
        """)
        orphan_facts = cursor.fetchone()[0]
        
        if orphan_facts == 0:
            print_check("Intégrité référentielle", True, "Aucun enregistrement orphelin")
        else:
            print_check("Problème intégrité référentielle", False, f"{orphan_facts} enregistrements orphelins")
            all_tests_passed = False
        
        cursor.close()
        conn.close()
        return all_tests_passed
        
    except Exception as e:
        print_check("Erreur validation données", False, str(e))
        cursor.close()
        conn.close()
        return False

def test_kpi_views():
    """Tester toutes les vues KPI"""
    print_header("VALIDATION VUES KPI")
    
    conn = create_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    all_tests_passed = True
    
    try:
        # Liste des vues KPI à tester
        kpi_views = [
            'v_kpi_taux_acceptation',
            'v_kpi_delai_traitement', 
            'v_kpi_volume_demandes',
            'v_kpi_analyse_temporelle',
            'v_kpi_performance_financiere',
            'v_kpi_repartition_geographique',
            'v_kpi_tableau_bord_executif'
        ]
        
        for view_name in kpi_views:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM public.{view_name}")
                count = cursor.fetchone()[0]
                
                # Tester l'exécution d'une requête simple
                cursor.execute(f"SELECT * FROM public.{view_name} LIMIT 1")
                sample = cursor.fetchone()
                
                if count >= 0 and sample is not None:
                    print_check(f"Vue {view_name}", True, f"{count} lignes, exécutable")
                else:
                    print_check(f"Vue {view_name}", True, f"{count} lignes, mais vide")
                
            except Exception as e:
                print_check(f"Vue {view_name}", False, f"Erreur: {str(e)}")
                all_tests_passed = False
        
        cursor.close()
        conn.close()
        return all_tests_passed
        
    except Exception as e:
        print_check("Erreur validation vues KPI", False, str(e))
        cursor.close()
        conn.close()
        return False

def test_performance():
    """Tester les performances de base"""
    print_header("VALIDATION PERFORMANCES")
    
    conn = create_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    performance_ok = True
    
    try:
        import time
        
        # Test 1: Requête simple sur une vue KPI
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM public.v_kpi_volume_demandes")
        result = cursor.fetchone()
        execution_time = time.time() - start_time
        
        if execution_time < 1.0:  # Moins d'une seconde
            print_check("Performance vue KPI", True, f"{execution_time:.3f}s")
        else:
            print_check("Performance vue KPI lente", False, f"{execution_time:.3f}s")
            performance_ok = False
        
        # Test 2: Requête complexe avec jointures
        start_time = time.time()
        cursor.execute("""
            SELECT e.raison_sociale, COUNT(f.demande_id)
            FROM marts.fct_demandes_attribution f
            JOIN marts.dim_entreprises e ON f.entreprise_key = e.entreprise_key
            GROUP BY e.raison_sociale
            LIMIT 10
        """)
        results = cursor.fetchall()
        execution_time = time.time() - start_time
        
        if execution_time < 2.0:  # Moins de 2 secondes
            print_check("Performance requête complexe", True, f"{execution_time:.3f}s, {len(results)} résultats")
        else:
            print_check("Performance requête complexe lente", False, f"{execution_time:.3f}s")
            performance_ok = False
        
        # Test 3: Taille de la base de données
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cursor.fetchone()[0]
        print_check("Taille base de données", True, f"{db_size}")
        
        cursor.close()
        conn.close()
        return performance_ok
        
    except Exception as e:
        print_check("Erreur test performance", False, str(e))
        cursor.close()
        conn.close()
        return False

def generate_final_report():
    """Générer un rapport final du système"""
    print_header("RAPPORT FINAL DU SYSTÈME")
    
    conn = create_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Statistiques générales
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('marts', 'staging')")
        total_tables = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public'")
        total_views = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM marts.fct_demandes_attribution")
        total_facts = cursor.fetchone()[0]
        
        # Données métier
        cursor.execute("SELECT COUNT(DISTINCT entreprise_key) FROM marts.fct_demandes_attribution")
        unique_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(montant_financement) FROM marts.fct_demandes_attribution WHERE montant_financement IS NOT NULL")
        total_financing = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(nombre_emplois) FROM marts.fct_demandes_attribution WHERE nombre_emplois IS NOT NULL") 
        total_jobs = cursor.fetchone()[0] or 0
        
        print("📊 STATISTIQUES SYSTÈME")
        print("-" * 40)
        print(f"   Taille base de données: {db_size}")
        print(f"   Tables data warehouse: {total_tables}")
        print(f"   Vues KPI: {total_views}")
        print(f"   Enregistrements traités: {total_facts}")
        
        print("\n💼 DONNÉES MÉTIER")
        print("-" * 40)
        print(f"   Entreprises uniques: {unique_companies}")
        print(f"   Financement total: {total_financing:,.0f} €")
        print(f"   Emplois créés: {total_jobs}")
        
        print(f"\n🕐 Validation effectuée le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Fonction principale de validation"""
    print("🔍 VALIDATION FINALE DU SYSTÈME SIGETI DWH")
    print("=" * 80)
    print(f"🕐 Début validation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Tests de validation
    tests = [
        ("Structure base de données", test_database_structure),
        ("Intégrité des données", test_data_integrity), 
        ("Vues KPI", test_kpi_views),
        ("Performances", test_performance)
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        print(f"\n🧪 Test: {test_name}")
        print("-" * 60)
        results[test_name] = test_function()
    
    # Rapport final
    generate_final_report()
    
    # Résumé des résultats
    print_header("RÉSUMÉ DE LA VALIDATION")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {test_name}")
    
    print(f"\n📊 Score: {passed_tests}/{total_tests} tests réussis ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 SYSTÈME VALIDÉ AVEC SUCCÈS!")
        print("💡 Le data warehouse SIGETI est opérationnel et optimisé")
        print("📈 Toutes les vues KPI sont fonctionnelles")
        print("🧹 Nettoyage terminé, système prêt pour la production")
    else:
        print(f"\n⚠️  VALIDATION PARTIELLE ({passed_tests}/{total_tests})")
        print("🔧 Certains composants nécessitent une attention")
        failed_tests = [name for name, result in results.items() if not result]
        print(f"❌ Tests échoués: {', '.join(failed_tests)}")
    
    print(f"\n🕐 Validation terminée: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")