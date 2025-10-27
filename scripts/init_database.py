#!/usr/bin/env python3
"""
Script d'initialisation de la base de données SIGETI DWH
Crée automatiquement :
- Base de données sigeti_dwh (si elle n'existe pas)
- Utilisateur sigeti_user (si il n'existe pas)
- Permissions appropriées
- Structure de base (schémas, extensions)
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from typing import Optional, Dict, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Classe pour initialiser la base de données SIGETI DWH"""
    
    def __init__(self):
        self.admin_config = {
            'host': os.getenv('SIGETI_NODE_DB_HOST', 'host.docker.internal'),
            'port': int(os.getenv('SIGETI_NODE_DB_PORT', '5432')),
            'user': os.getenv('SIGETI_NODE_DB_USER', 'postgres'),
            'password': os.getenv('SIGETI_NODE_DB_PASSWORD', 'postgres'),
            'database': 'postgres'  # Base système pour créer d'autres bases
        }
        
        self.target_db = os.getenv('SIGETI_DB_NAME', 'sigeti_dwh')
        self.target_user = os.getenv('SIGETI_DB_USER', 'sigeti_user')
        self.target_password = os.getenv('SIGETI_DB_PASSWORD', 'sigeti123')
        
    def get_admin_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Connexion en tant qu'administrateur PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.admin_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("✅ Connexion admin PostgreSQL établie")
            return conn
        except Exception as e:
            logger.error(f"❌ Erreur connexion admin: {e}")
            return None
    
    def database_exists(self, cursor, db_name: str) -> bool:
        """Vérifier si une base de données existe"""
        try:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", 
                (db_name,)
            )
            exists = cursor.fetchone() is not None
            logger.info(f"🔍 Base '{db_name}': {'EXISTE' if exists else 'N EXISTE PAS'}")
            return exists
        except Exception as e:
            logger.error(f"❌ Erreur vérification base '{db_name}': {e}")
            return False
    
    def user_exists(self, cursor, username: str) -> bool:
        """Vérifier si un utilisateur existe"""
        try:
            cursor.execute(
                "SELECT 1 FROM pg_user WHERE usename = %s", 
                (username,)
            )
            exists = cursor.fetchone() is not None
            logger.info(f"🔍 Utilisateur '{username}': {'EXISTE' if exists else 'N EXISTE PAS'}")
            return exists
        except Exception as e:
            logger.error(f"❌ Erreur vérification utilisateur '{username}': {e}")
            return False
    
    def create_user(self, cursor, username: str, password: str) -> bool:
        """Créer un utilisateur PostgreSQL"""
        try:
            cursor.execute(f"""
                CREATE USER {username} 
                WITH PASSWORD %s 
                CREATEDB 
                LOGIN;
            """, (password,))
            logger.info(f"✅ Utilisateur '{username}' créé avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création utilisateur '{username}': {e}")
            return False
    
    def create_database(self, cursor, db_name: str, owner: str) -> bool:
        """Créer une base de données"""
        try:
            cursor.execute(f"""
                CREATE DATABASE {db_name} 
                WITH OWNER = {owner}
                ENCODING = 'UTF8'
                LC_COLLATE = 'French_France.1252'
                LC_CTYPE = 'French_France.1252'
                TEMPLATE = template0;
            """)
            logger.info(f"✅ Base de données '{db_name}' créée avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création base '{db_name}': {e}")
            return False
    
    def grant_permissions(self, cursor, db_name: str, username: str) -> bool:
        """Accorder les permissions sur la base"""
        try:
            # Permissions sur la base
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username};")
            
            # Connexion à la base cible pour permissions sur schémas
            target_config = self.admin_config.copy()
            target_config['database'] = db_name
            
            with psycopg2.connect(**target_config) as target_conn:
                target_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with target_conn.cursor() as target_cursor:
                    # Permissions sur le schéma public
                    target_cursor.execute(f"GRANT ALL ON SCHEMA public TO {username};")
                    target_cursor.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {username};")
                    target_cursor.execute(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {username};")
                    target_cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {username};")
            
            logger.info(f"✅ Permissions accordées à '{username}' sur '{db_name}'")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur permissions '{username}' sur '{db_name}': {e}")
            return False
    
    def setup_database_structure(self, db_name: str) -> bool:
        """Configurer la structure de base de la DB"""
        try:
            # Connexion à la base cible
            target_config = self.admin_config.copy()
            target_config['database'] = db_name
            
            with psycopg2.connect(**target_config) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    
                    # Créer les extensions nécessaires
                    extensions = ['uuid-ossp', 'btree_gin', 'pg_trgm']
                    
                    for ext in extensions:
                        try:
                            cursor.execute(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\";")
                            logger.info(f"✅ Extension '{ext}' installée")
                        except Exception as e:
                            logger.warning(f"⚠️  Extension '{ext}' non installée: {e}")
                    
                    # Créer les schémas de base
                    schemas = ['staging', 'marts', 'analytics', 'dwh', 'reporting']
                    
                    for schema in schemas:
                        try:
                            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
                            cursor.execute(f"GRANT ALL ON SCHEMA {schema} TO {self.target_user};")
                            logger.info(f"✅ Schéma '{schema}' créé")
                        except Exception as e:
                            logger.error(f"❌ Erreur schéma '{schema}': {e}")
            
            logger.info(f"✅ Structure de base configurée pour '{db_name}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur configuration structure: {e}")
            return False
    
    def test_user_connection(self) -> bool:
        """Tester la connexion avec l'utilisateur créé"""
        try:
            test_config = {
                'host': self.admin_config['host'],
                'port': self.admin_config['port'],
                'database': self.target_db,
                'user': self.target_user,
                'password': self.target_password
            }
            
            with psycopg2.connect(**test_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user, version();")
                    db, user, version = cursor.fetchone()
                    logger.info(f"✅ Test connexion réussi - DB: {db}, User: {user}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Erreur test connexion utilisateur: {e}")
            return False
    
    def initialize_all(self) -> bool:
        """Initialisation complète de la base SIGETI DWH"""
        logger.info("🚀 Début initialisation base SIGETI DWH")
        
        conn = self.get_admin_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                success = True
                
                # 1. Créer l'utilisateur si nécessaire
                if not self.user_exists(cursor, self.target_user):
                    logger.info(f"👤 Création de l'utilisateur '{self.target_user}'...")
                    if not self.create_user(cursor, self.target_user, self.target_password):
                        success = False
                else:
                    logger.info(f"👤 Utilisateur '{self.target_user}' déjà existant")
                
                # 2. Créer la base de données si nécessaire
                if not self.database_exists(cursor, self.target_db):
                    logger.info(f"🗄️  Création de la base '{self.target_db}'...")
                    if not self.create_database(cursor, self.target_db, self.target_user):
                        success = False
                else:
                    logger.info(f"🗄️  Base '{self.target_db}' déjà existante")
                
                # 3. Accorder les permissions
                logger.info("🔐 Configuration des permissions...")
                if not self.grant_permissions(cursor, self.target_db, self.target_user):
                    success = False
            
            # 4. Configurer la structure de base
            logger.info("🏗️  Configuration de la structure...")
            if not self.setup_database_structure(self.target_db):
                success = False
            
            # 5. Tester la connexion finale
            logger.info("🧪 Test de connexion final...")
            if not self.test_user_connection():
                success = False
            
            if success:
                logger.info("🎉 Initialisation terminée avec succès!")
            else:
                logger.error("❌ Initialisation partiellement échouée")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur générale initialisation: {e}")
            return False
        
        finally:
            conn.close()

def main():
    """Point d'entrée principal"""
    logger.info("=" * 60)
    logger.info("🐳 SIGETI DWH - Initialisation Base de Données")
    logger.info("=" * 60)
    
    try:
        initializer = DatabaseInitializer()
        
        # Afficher la configuration
        logger.info("📋 Configuration:")
        logger.info(f"   Host: {initializer.admin_config['host']}:{initializer.admin_config['port']}")
        logger.info(f"   Base cible: {initializer.target_db}")
        logger.info(f"   Utilisateur cible: {initializer.target_user}")
        logger.info("")
        
        # Lancer l'initialisation
        success = initializer.initialize_all()
        
        if success:
            logger.info("✅ Base SIGETI DWH prête pour l'ETL!")
            sys.exit(0)
        else:
            logger.error("❌ Échec de l'initialisation")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️  Initialisation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()