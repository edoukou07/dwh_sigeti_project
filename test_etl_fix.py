#!/usr/bin/env python3
"""Test rapide des corrections ETL"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Configuration pour les tests
os.environ.update({
    'POSTGRES_HOST': 'host.docker.internal',
    'POSTGRES_PORT': '5432',
    'POSTGRES_DB': 'sigeti_dwh',
    'POSTGRES_USER': 'sigeti_user',
    'POSTGRES_PASSWORD': 'sigeti123'
})

def test_sqlalchemy_connection():
    """Test de la connexion SQLAlchemy avec begin()"""
    print("🧪 Test de la connexion SQLAlchemy...")
    
    try:
        # Configuration DWH
        dwh_config = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT')),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        connection_string = f"postgresql://{dwh_config['user']}:{dwh_config['password']}@{dwh_config['host']}:{dwh_config['port']}/{dwh_config['database']}"
        engine = create_engine(connection_string)
        
        # Test avec begin() au lieu de connect()
        with engine.begin() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ Connexion SQLAlchemy réussie - Valeur test: {test_value}")
        
        # Test de création de table (simulation)
        test_sql = """
        CREATE TABLE IF NOT EXISTS staging.test_table (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(100)
        )
        """
        
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
            conn.execute(text(test_sql))
            print("✅ Test création table staging réussi")
        
        # Nettoyage
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS staging.test_table"))
            print("✅ Nettoyage réussi")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur test SQLAlchemy: {e}")
        return False

def main():
    print("🚀 TEST DES CORRECTIONS ETL")
    print("=" * 40)
    
    if test_sqlalchemy_connection():
        print("\n✅ TOUTES LES CORRECTIONS FONCTIONNENT!")
        print("🎯 Vous pouvez maintenant relancer votre DAG Airflow")
    else:
        print("\n❌ Des corrections supplémentaires sont nécessaires")

if __name__ == "__main__":
    main()