#!/usr/bin/env python3
"""
Script de test pour l'initialisation de la base de données SIGETI
Valide que la base et les utilisateurs sont correctement créés
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration par défaut
DEFAULT_CONFIG = {
    'NODE_HOST': 'localhost',
    'NODE_PORT': '5432',
    'NODE_USER': 'postgres',
    'NODE_PASSWORD': 'postgres',
    'SIGETI_DB': 'sigeti_dwh',
    'SIGETI_USER': 'sigeti_user',
    'SIGETI_PASSWORD': 'sigeti123'
}

def get_config():
    """Récupère la configuration depuis les variables d'environnement ou utilise les valeurs par défaut"""
    config = {}
    for key, default_value in DEFAULT_CONFIG.items():
        env_key = f'SIGETI_{key}' if not key.startswith('NODE_') else f'SIGETI_{key}'
        config[key] = os.getenv(env_key, default_value)
    return config

def test_admin_connection(config):
    """Test la connexion administrateur"""
    print("🔍 Test de connexion administrateur...")
    try:
        conn = psycopg2.connect(
            host=config['NODE_HOST'],
            port=config['NODE_PORT'],
            user=config['NODE_USER'],
            password=config['NODE_PASSWORD'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Connexion administrateur réussie")
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion administrateur: {e}")
        return None

def test_database_exists(conn, db_name):
    """Vérifie si la base de données existe"""
    print(f"🔍 Vérification de l'existence de la base '{db_name}'...")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone() is not None
        cursor.close()
        
        if exists:
            print(f"✅ Base de données '{db_name}' existe")
        else:
            print(f"❌ Base de données '{db_name}' n'existe pas")
        return exists
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la base: {e}")
        return False

def test_user_exists(conn, username):
    """Vérifie si l'utilisateur existe"""
    print(f"🔍 Vérification de l'existence de l'utilisateur '{username}'...")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = %s", (username,))
        exists = cursor.fetchone() is not None
        cursor.close()
        
        if exists:
            print(f"✅ Utilisateur '{username}' existe")
        else:
            print(f"❌ Utilisateur '{username}' n'existe pas")
        return exists
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de l'utilisateur: {e}")
        return False

def test_user_connection(config):
    """Test la connexion avec l'utilisateur SIGETI"""
    print(f"🔍 Test de connexion utilisateur '{config['SIGETI_USER']}'...")
    try:
        conn = psycopg2.connect(
            host=config['NODE_HOST'],
            port=config['NODE_PORT'],
            user=config['SIGETI_USER'],
            password=config['SIGETI_PASSWORD'],
            database=config['SIGETI_DB']
        )
        print(f"✅ Connexion utilisateur '{config['SIGETI_USER']}' réussie")
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion utilisateur: {e}")
        return None

def test_user_permissions(conn):
    """Test les permissions de l'utilisateur"""
    print("🔍 Test des permissions utilisateur...")
    try:
        cursor = conn.cursor()
        
        # Test création de table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_permissions (
                id SERIAL PRIMARY KEY,
                test_data VARCHAR(50)
            )
        """)
        print("✅ Permission CREATE TABLE: OK")
        
        # Test insertion
        cursor.execute("INSERT INTO test_permissions (test_data) VALUES (%s)", ("test",))
        print("✅ Permission INSERT: OK")
        
        # Test lecture
        cursor.execute("SELECT COUNT(*) FROM test_permissions")
        count = cursor.fetchone()[0]
        print(f"✅ Permission SELECT: OK ({count} enregistrements)")
        
        # Nettoyage
        cursor.execute("DROP TABLE IF EXISTS test_permissions")
        print("✅ Permission DROP TABLE: OK")
        
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Erreur de permissions: {e}")
        return False

def test_database_schemas(conn):
    """Vérifie les schémas de la base de données"""
    print("🔍 Vérification des schémas...")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('staging', 'marts', 'analytics')
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_schemas = ['staging', 'marts', 'analytics']
        for schema in expected_schemas:
            if schema in schemas:
                print(f"✅ Schéma '{schema}': existe")
            else:
                print(f"❌ Schéma '{schema}': manquant")
        
        return len(schemas) == len(expected_schemas)
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des schémas: {e}")
        return False

def run_tests():
    """Exécute tous les tests"""
    print("="*60)
    print("🧪 TESTS D'INITIALISATION BASE DE DONNÉES SIGETI")
    print("="*60)
    
    config = get_config()
    print("\n📋 Configuration:")
    for key, value in config.items():
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    
    all_tests_passed = True
    
    # Test 1: Connexion administrateur
    print("\n" + "="*40)
    print("TEST 1: Connexion Administrateur")
    print("="*40)
    admin_conn = test_admin_connection(config)
    if not admin_conn:
        print("❌ Impossible de continuer sans connexion administrateur")
        return False
    
    # Test 2: Existence de la base de données
    print("\n" + "="*40)
    print("TEST 2: Base de Données")
    print("="*40)
    db_exists = test_database_exists(admin_conn, config['SIGETI_DB'])
    all_tests_passed = all_tests_passed and db_exists
    
    # Test 3: Existence de l'utilisateur
    print("\n" + "="*40)
    print("TEST 3: Utilisateur")
    print("="*40)
    user_exists = test_user_exists(admin_conn, config['SIGETI_USER'])
    all_tests_passed = all_tests_passed and user_exists
    
    admin_conn.close()
    
    if not (db_exists and user_exists):
        print("\n❌ Tests d'existence échoués - arrêt des tests")
        return False
    
    # Test 4: Connexion utilisateur
    print("\n" + "="*40)
    print("TEST 4: Connexion Utilisateur")
    print("="*40)
    user_conn = test_user_connection(config)
    if not user_conn:
        all_tests_passed = False
    else:
        # Test 5: Permissions
        print("\n" + "="*40)
        print("TEST 5: Permissions")
        print("="*40)
        permissions_ok = test_user_permissions(user_conn)
        all_tests_passed = all_tests_passed and permissions_ok
        
        # Test 6: Schémas
        print("\n" + "="*40)
        print("TEST 6: Schémas")
        print("="*40)
        schemas_ok = test_database_schemas(user_conn)
        all_tests_passed = all_tests_passed and schemas_ok
        
        user_conn.close()
    
    # Résumé
    print("\n" + "="*60)
    print("🎯 RÉSUMÉ DES TESTS")
    print("="*60)
    if all_tests_passed:
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("🚀 Base de données prête pour le pipeline SIGETI")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Vérifiez la configuration et relancez l'initialisation")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)