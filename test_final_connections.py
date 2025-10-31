#!/usr/bin/env python3
"""Test des connexions avec les nouvelles variables"""

import os
import psycopg2
from sqlalchemy import create_engine

def test_connections():
    print("🧪 TEST DES CONNEXIONS AVEC VARIABLES D'ENVIRONNEMENT")
    print("=" * 55)
    
    # Test connexion source avec les variables disponibles
    print("\n📊 Test connexion BASE SOURCE (sigeti_node_db):")
    source_config = {
        'host': os.getenv('SIGETI_NODE_DB_HOST', os.getenv('DB_SOURCE_HOST', 'localhost')),
        'port': int(os.getenv('SIGETI_NODE_DB_PORT', os.getenv('DB_SOURCE_PORT', 5432))),
        'database': os.getenv('SIGETI_NODE_DB_NAME', os.getenv('DB_SOURCE_NAME', 'sigeti_node_db')),
        'user': os.getenv('SIGETI_NODE_DB_USER', os.getenv('DB_SOURCE_USER', 'postgres')),
        'password': os.getenv('SIGETI_NODE_DB_PASSWORD', os.getenv('DB_SOURCE_PASSWORD', 'postgres'))
    }
    
    print(f"   Host: {source_config['host']}")
    print(f"   Database: {source_config['database']}")
    print(f"   User: {source_config['user']}")
    
    try:
        conn_source = psycopg2.connect(**source_config)
        cursor = conn_source.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn_source.close()
        print(f"   ✅ Connexion source réussie: {version}")
        source_ok = True
    except Exception as e:
        print(f"   ❌ Erreur connexion source: {e}")
        source_ok = False
    
    # Test connexion DWH
    print("\n🏪 Test connexion DWH (sigeti_dwh):")
    dwh_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'sigeti_dwh'),
        'user': os.getenv('POSTGRES_USER', 'sigeti_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'sigeti123')
    }
    
    print(f"   Host: {dwh_config['host']}")
    print(f"   Database: {dwh_config['database']}")
    print(f"   User: {dwh_config['user']}")
    
    try:
        conn_dwh = psycopg2.connect(**dwh_config)
        cursor = conn_dwh.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn_dwh.close()
        print(f"   ✅ Connexion DWH réussie: {version}")
        dwh_ok = True
    except Exception as e:
        print(f"   ❌ Erreur connexion DWH: {e}")
        dwh_ok = False
    
    # Résultat
    print(f"\n🎯 RÉSULTATS:")
    if source_ok and dwh_ok:
        print("   ✅ TOUTES LES CONNEXIONS FONCTIONNENT!")
        print("   🚀 L'ETL peut maintenant s'exécuter")
        return True
    else:
        print("   ❌ Des problèmes de connexion persistent")
        if not source_ok:
            print("   📊 Problème avec la base source")
        if not dwh_ok:
            print("   🏪 Problème avec la base DWH")
        return False

if __name__ == "__main__":
    test_connections()