"""
Script de nettoyage des bases de données SIGETI
Supprime les schémas et données non utilisés pour optimiser l'espace
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from datetime import datetime

# Configuration des bases de données
DB_CONFIGS = {
    'sigeti_dwh': {
        'host': 'localhost',
        'database': 'sigeti_dwh',
        'user': 'postgres',
        'password': 'postgres',
        'port': 5432
    },
    'sigeti_node_db': {
        'host': 'localhost', 
        'database': 'sigeti_node_db',
        'user': 'postgres',
        'password': 'postgres',
        'port': 5432
    }
}

def print_header(title):
    """Afficher un titre formaté"""
    print("\n" + "="*60)
    print(f"🧹 {title}")
    print("="*60)

def print_step(step_name, status="INFO"):
    """Afficher une étape"""
    if status == "INFO":
        print(f"ℹ️  {step_name}")
    elif status == "SUCCESS":
        print(f"✅ {step_name}")
    elif status == "WARNING":
        print(f"⚠️  {step_name}")
    elif status == "ERROR":
        print(f"❌ {step_name}")

def create_connection(db_name):
    """Créer une connexion à la base de données"""
    try:
        config = DB_CONFIGS[db_name]
        conn = psycopg2.connect(**config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print_step(f"Erreur connexion {db_name}: {e}", "ERROR")
        return None

def get_database_info(db_name):
    """Obtenir les informations sur une base de données"""
    conn = create_connection(db_name)
    if not conn:
        return None
    
    cursor = conn.cursor()
    info = {}
    
    try:
        # Schémas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name
        """)
        info['schemas'] = [row[0] for row in cursor.fetchall()]
        
        # Tables par schéma
        info['tables'] = {}
        for schema in info['schemas']:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))
            info['tables'][schema] = [row[0] for row in cursor.fetchall()]
        
        # Vues par schéma
        info['views'] = {}
        for schema in info['schemas']:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema,))
            info['views'][schema] = [row[0] for row in cursor.fetchall()]
        
        # Taille de la base
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        info['size'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        return info
        
    except Exception as e:
        print_step(f"Erreur récupération infos {db_name}: {e}", "ERROR")
        cursor.close()
        conn.close()
        return None

def clean_sigeti_dwh():
    """Nettoyer la base sigeti_dwh"""
    print_header("NETTOYAGE SIGETI_DWH")
    
    conn = create_connection('sigeti_dwh')
    if not conn:
        return False
    
    cursor = conn.cursor()
    cleaned_items = []
    
    try:
        # 1. Supprimer le schéma sigeti_source s'il est vide
        print_step("Vérification du schéma sigeti_source...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sigeti_source'
        """)
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            cursor.execute("DROP SCHEMA IF EXISTS sigeti_source CASCADE")
            print_step("Schéma sigeti_source supprimé (vide)", "SUCCESS")
            cleaned_items.append("Schéma sigeti_source")
        else:
            print_step(f"Schéma sigeti_source conservé ({table_count} tables)", "INFO")
        
        # 2. Nettoyer les tables temporaires ou inutiles dans public
        print_step("Nettoyage des tables temporaires dans public...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND (table_name LIKE 'temp_%' OR table_name LIKE 'tmp_%' OR table_name LIKE 'test_%')
        """)
        temp_tables = cursor.fetchall()
        
        for table in temp_tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS public.{table_name} CASCADE")
            print_step(f"Table temporaire supprimée: {table_name}", "SUCCESS")
            cleaned_items.append(f"Table public.{table_name}")
        
        # 3. Supprimer les vues orphelines (non KPI)
        print_step("Vérification des vues orphelines...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public' 
            AND table_name NOT LIKE 'v_kpi_%'
        """)
        orphan_views = cursor.fetchall()
        
        for view in orphan_views:
            view_name = view[0]
            cursor.execute(f"DROP VIEW IF EXISTS public.{view_name} CASCADE")
            print_step(f"Vue orpheline supprimée: {view_name}", "SUCCESS")
            cleaned_items.append(f"Vue public.{view_name}")
        
        # 4. Nettoyer les index inutiles
        print_step("Vérification des index inutiles...")
        cursor.execute("""
            SELECT schemaname, indexname, tablename
            FROM pg_indexes 
            WHERE schemaname IN ('staging', 'marts', 'public')
            AND indexname NOT LIKE '%_pkey'
            AND indexname NOT LIKE 'pg_%'
        """)
        custom_indexes = cursor.fetchall()
        
        for schema, index_name, table_name in custom_indexes:
            # Garder seulement les index sur les clés étrangères importantes
            if any(key in index_name.lower() for key in ['_key', 'fk_', 'idx_date']):
                print_step(f"Index conservé: {schema}.{index_name}", "INFO")
            else:
                cursor.execute(f"DROP INDEX IF EXISTS {schema}.{index_name}")
                print_step(f"Index supprimé: {schema}.{index_name}", "SUCCESS")
                cleaned_items.append(f"Index {schema}.{index_name}")
        
        # 5. VACUUM ANALYZE pour récupérer l'espace
        print_step("Optimisation de l'espace disque (VACUUM)...")
        cursor.execute("VACUUM ANALYZE")
        print_step("VACUUM ANALYZE terminé", "SUCCESS")
        
        cursor.close()
        conn.close()
        
        print_step(f"Nettoyage sigeti_dwh terminé: {len(cleaned_items)} éléments supprimés", "SUCCESS")
        return True
        
    except Exception as e:
        print_step(f"Erreur nettoyage sigeti_dwh: {e}", "ERROR")
        cursor.close()
        conn.close()
        return False

def clean_sigeti_node_db():
    """Nettoyer la base sigeti_node_db (source)"""
    print_header("NETTOYAGE SIGETI_NODE_DB")
    
    conn = create_connection('sigeti_node_db')
    if not conn:
        return False
    
    cursor = conn.cursor()
    cleaned_items = []
    
    try:
        # 1. Supprimer les tables de test ou temporaires
        print_step("Recherche de tables temporaires...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND (table_name LIKE 'temp_%' OR table_name LIKE 'tmp_%' 
                 OR table_name LIKE 'test_%' OR table_name LIKE 'backup_%')
        """)
        temp_tables = cursor.fetchall()
        
        for table in temp_tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print_step(f"Table temporaire supprimée: {table_name}", "SUCCESS")
            cleaned_items.append(f"Table {table_name}")
        
        # 2. Nettoyer les données de test (optionnel - à activer si nécessaire)
        # ATTENTION: Décommentez seulement si vous voulez supprimer les données de test
        """
        print_step("Suppression des données de test...")
        cursor.execute("DELETE FROM demandes_attribution WHERE reference LIKE 'TEST%'")
        cursor.execute("DELETE FROM entreprises WHERE nom LIKE 'Test%'")
        test_deleted = cursor.rowcount
        print_step(f"Données de test supprimées: {test_deleted} lignes", "SUCCESS")
        """
        
        # 3. VACUUM ANALYZE
        print_step("Optimisation de l'espace disque (VACUUM)...")
        cursor.execute("VACUUM ANALYZE")
        print_step("VACUUM ANALYZE terminé", "SUCCESS")
        
        cursor.close()
        conn.close()
        
        print_step(f"Nettoyage sigeti_node_db terminé: {len(cleaned_items)} éléments supprimés", "SUCCESS")
        return True
        
    except Exception as e:
        print_step(f"Erreur nettoyage sigeti_node_db: {e}", "ERROR")
        cursor.close()
        conn.close()
        return False

def optimize_database_settings():
    """Optimiser les paramètres des bases de données"""
    print_header("OPTIMISATION DES PARAMÈTRES")
    
    optimizations = [
        "SET maintenance_work_mem = '256MB'",
        "SET checkpoint_completion_target = 0.9", 
        "SET wal_buffers = '16MB'",
        "SET default_statistics_target = 100"
    ]
    
    for db_name in ['sigeti_dwh', 'sigeti_node_db']:
        conn = create_connection(db_name)
        if conn:
            cursor = conn.cursor()
            try:
                for sql in optimizations:
                    cursor.execute(sql)
                print_step(f"Paramètres optimisés pour {db_name}", "SUCCESS")
            except Exception as e:
                print_step(f"Erreur optimisation {db_name}: {e}", "WARNING")
            finally:
                cursor.close()
                conn.close()

def generate_cleanup_report():
    """Générer un rapport de nettoyage"""
    print_header("RAPPORT DE NETTOYAGE")
    
    for db_name in ['sigeti_dwh', 'sigeti_node_db']:
        print(f"\n📊 Base de données: {db_name}")
        print("-" * 40)
        
        info = get_database_info(db_name)
        if info:
            print(f"   Taille totale: {info['size']}")
            print(f"   Schémas: {len(info['schemas'])}")
            
            total_tables = sum(len(tables) for tables in info['tables'].values())
            total_views = sum(len(views) for views in info['views'].values())
            
            print(f"   Tables: {total_tables}")
            print(f"   Vues: {total_views}")
            
            # Détail par schéma
            for schema in info['schemas']:
                if info['tables'][schema] or info['views'][schema]:
                    print(f"   └── {schema}: {len(info['tables'][schema])} tables, {len(info['views'][schema])} vues")

def backup_before_cleanup():
    """Créer une sauvegarde avant nettoyage"""
    print_header("SAUVEGARDE PRÉVENTIVE")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = r"c:\Users\hynco\Desktop\SIGETI_DWH\backups"
    
    try:
        import os
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder seulement les vues KPI (plus léger)
        backup_file = f"{backup_dir}\\kpi_views_backup_{timestamp}.sql"
        
        print_step(f"Sauvegarde des vues KPI dans: {backup_file}", "INFO")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("-- Sauvegarde des vues KPI SIGETI\n")
            f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            conn = create_connection('sigeti_dwh')
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT definition 
                    FROM pg_views 
                    WHERE schemaname = 'public' 
                    AND viewname LIKE 'v_kpi_%'
                    ORDER BY viewname
                """)
                
                for definition in cursor.fetchall():
                    f.write(f"CREATE OR REPLACE VIEW {definition[0]};\n\n")
                
                cursor.close()
                conn.close()
        
        print_step("Sauvegarde créée avec succès", "SUCCESS")
        return True
        
    except Exception as e:
        print_step(f"Erreur sauvegarde: {e}", "ERROR")
        return False

def main():
    """Fonction principale de nettoyage"""
    print("🧹 NETTOYAGE DES BASES DE DONNÉES SIGETI")
    print("=" * 80)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette opération va supprimer des données!")
    print("   - Schémas vides")
    print("   - Tables temporaires")  
    print("   - Vues orphelines")
    print("   - Index inutiles")
    
    response = input("\nContinuer? (oui/non): ").lower().strip()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("🚫 Nettoyage annulé par l'utilisateur")
        return
    
    # Rapport initial
    print_header("ÉTAT INITIAL")
    generate_cleanup_report()
    
    # Sauvegarde préventive
    if not backup_before_cleanup():
        print("⚠️  Sauvegarde échouée, continuer quand même? (oui/non): ", end="")
        if input().lower().strip() not in ['oui', 'o', 'yes', 'y']:
            return
    
    # Nettoyage
    success_count = 0
    
    if clean_sigeti_dwh():
        success_count += 1
    
    if clean_sigeti_node_db():
        success_count += 1
    
    # Optimisation
    optimize_database_settings()
    
    # Rapport final
    print_header("ÉTAT FINAL")
    generate_cleanup_report()
    
    # Résumé
    print_header("RÉSUMÉ")
    print(f"✅ Bases nettoyées avec succès: {success_count}/2")
    print(f"🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == 2:
        print("\n🎉 Nettoyage terminé avec succès!")
        print("💡 Conseils:")
        print("   - Redémarrez PostgreSQL pour appliquer les optimisations")
        print("   - Surveillez les performances après nettoyage")
        print("   - Programmez des nettoyages réguliers")
    else:
        print("\n⚠️  Nettoyage partiellement réussi")
        print("   Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Nettoyage interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
    finally:
        print(f"\n🕐 Session terminée: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")