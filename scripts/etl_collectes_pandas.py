#!/usr/bin/env python3
"""
ETL pour les données de Collectes et Recouvrement SIGETI
Script d'extraction, transformation et chargement des données de collectes
depuis la base source vers le data warehouse
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ETLCollectesRecouvrements:
    """Classe pour l'ETL des collectes et recouvrements"""
    
    def __init__(self):
        """Initialisation de l'ETL"""
        # Configuration de la base source LOCALE SIGETI_NODE
        self.source_config = {
            'host': os.getenv('SIGETI_NODE_DB_HOST', os.getenv('DB_SOURCE_HOST', 'localhost')),
            'port': int(os.getenv('SIGETI_NODE_DB_PORT', os.getenv('DB_SOURCE_PORT', 5432))),
            'database': os.getenv('SIGETI_NODE_DB_NAME', os.getenv('DB_SOURCE_NAME', 'sigeti_node_db')),
            'user': os.getenv('SIGETI_NODE_DB_USER', os.getenv('DB_SOURCE_USER', 'postgres')),
            'password': os.getenv('SIGETI_NODE_DB_PASSWORD', os.getenv('DB_SOURCE_PASSWORD', 'postgres'))
        }
        
        # Configuration du data warehouse LOCAL SIGETI_DWH
        self.dwh_config = {
            'host': os.getenv('SIGETI_DB_HOST', os.getenv('DWH_DB_HOST', os.getenv('POSTGRES_HOST', 'localhost'))),
            'port': int(os.getenv('SIGETI_DB_PORT', os.getenv('DWH_DB_PORT', os.getenv('POSTGRES_PORT', 5432)))),
            'database': os.getenv('SIGETI_DB_NAME', os.getenv('DWH_DB_NAME', os.getenv('POSTGRES_DB', 'sigeti_dwh'))),
            'user': os.getenv('SIGETI_DB_USER', os.getenv('DWH_DB_USER', os.getenv('POSTGRES_USER', 'sigeti_user'))),
            'password': os.getenv('SIGETI_DB_PASSWORD', os.getenv('DWH_DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'sigeti123')))
        }
        
        self.source_engine = None
        self.dwh_engine = None
        
    def create_connections(self):
        """Créer les connexions aux bases de données"""
        try:
            # Connexion source
            source_url = f"postgresql://{self.source_config['user']}:{self.source_config['password']}@{self.source_config['host']}:{self.source_config['port']}/{self.source_config['database']}"
            self.source_engine = create_engine(source_url)
            
            # Connexion DWH
            dwh_url = f"postgresql://{self.dwh_config['user']}:{self.dwh_config['password']}@{self.dwh_config['host']}:{self.dwh_config['port']}/{self.dwh_config['database']}"
            self.dwh_engine = create_engine(dwh_url)
            
            logger.info("✅ Connexions aux bases de données établies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return False
    
    def extract_collectes_data(self) -> Optional[pd.DataFrame]:
        """Extraire les données de collectes depuis la base source"""
        try:
            query = """
            SELECT 
                id as collecte_id,
                reference,
                'RECOUVREMENT' as type_collecte,
                montant_a_recouvrer as montant_a_collecter,
                montant_recouvre as montant_collecte,
                status::text as statut_collecte,
                date_debut as date_creation,
                date_fin_prevue as date_echeance,
                NULL as date_recouvrement,
                cree_par as agent_collecteur_id,
                NULL as entreprise_id,
                NULL as lot_id,
                NULL as zone_id,
                NULL as demande_attribution_id,
                commentaire as observations,
                updated_at as date_modification
            FROM public.collectes
            ORDER BY created_at DESC
            """
            
            logger.info("📥 Extraction des données de collectes...")
            df = pd.read_sql(query, self.source_engine)
            logger.info(f"✅ {len(df)} enregistrements de collectes extraits")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction collectes: {e}")
            return None
    
    def extract_agents_collecteurs_data(self) -> Optional[pd.DataFrame]:
        """Extraire les données des agents collecteurs"""
        try:
            query = """
            SELECT 
                agent_id,
                CONCAT(nom, ' ', prenom) as nom_agent,
                matricule,
                'COLLECTEUR' as fonction,
                zone_assignee_id as zone_affectation_id,
                telephone,
                email,
                statut as statut_agent,
                date_embauche,
                date_creation,
                date_modification
            FROM public.agents_collecteurs
            WHERE statut = 'ACTIF'
               OR date_modification >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY nom, prenom
            """
            
            logger.info("📥 Extraction des données des agents collecteurs...")
            df = pd.read_sql(query, self.source_engine)
            logger.info(f"✅ {len(df)} agents collecteurs extraits")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction agents: {e}")
            return None
    
    def extract_recouvrements_data(self) -> Optional[pd.DataFrame]:
        """Extraire les données des actions de recouvrement"""
        try:
            query = """
            SELECT 
                recouvrement_id,
                collecte_id,
                type_action,
                date_action,
                montant_paiement,
                mode_paiement,
                agent_recouvrement_id,
                statut_recouvrement,
                observations,
                piece_justificative,
                date_creation,
                date_modification
            FROM public.recouvrements
            WHERE date_modification >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY date_action DESC
            """
            
            logger.info("📥 Extraction des données de recouvrement...")
            df = pd.read_sql(query, self.source_engine)
            logger.info(f"✅ {len(df)} actions de recouvrement extraites")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction recouvrements: {e}")
            return None
    
    def transform_collectes_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transformer les données de collectes"""
        try:
            logger.info("🔄 Transformation des données de collectes...")
            
            # Nettoyage des données
            df = df.copy()
            
            # Standardisation des types de collectes
            type_mapping = {
                'redevance': 'REDEVANCE',
                'impot': 'IMPOT', 
                'taxe': 'TAXE',
                'amende': 'AMENDE'
            }
            df['type_collecte'] = df['type_collecte'].str.lower().map(type_mapping).fillna(df['type_collecte'].str.upper())
            
            # Standardisation des statuts
            statut_mapping = {
                'en_attente': 'EN_ATTENTE',
                'partiellement_collecte': 'PARTIELLEMENT_COLLECTE',
                'totalement_collecte': 'TOTALEMENT_COLLECTE',
                'echec': 'ECHEC'
            }
            df['statut_collecte'] = df['statut_collecte'].str.lower().map(statut_mapping).fillna(df['statut_collecte'].str.upper())
            
            # Conversion des montants
            df['montant_a_collecter'] = pd.to_numeric(df['montant_a_collecter'], errors='coerce').fillna(0)
            df['montant_collecte'] = pd.to_numeric(df['montant_collecte'], errors='coerce').fillna(0)
            
            # Conversion des dates
            date_columns = ['date_creation', 'date_echeance', 'date_recouvrement', 'date_modification']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Validation des données
            df = df.dropna(subset=['collecte_id'])
            df = df[df['montant_a_collecter'] >= 0]
            
            logger.info(f"✅ {len(df)} enregistrements de collectes transformés")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur transformation collectes: {e}")
            return pd.DataFrame()
    
    def transform_agents_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transformer les données des agents"""
        try:
            logger.info("🔄 Transformation des données des agents...")
            
            df = df.copy()
            
            # Nettoyage des noms
            df['nom_agent'] = df['nom_agent'].str.strip().str.title()
            df['fonction'] = df['fonction'].str.strip().str.upper()
            
            # Standardisation du statut
            df['statut_agent'] = df['statut_agent'].str.upper()
            
            # Validation email
            df.loc[~df['email'].str.contains('@', na=False), 'email'] = None
            
            # Conversion des dates
            date_columns = ['date_embauche', 'date_creation', 'date_modification']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Validation
            df = df.dropna(subset=['agent_id', 'nom_agent'])
            
            logger.info(f"✅ {len(df)} agents transformés")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur transformation agents: {e}")
            return pd.DataFrame()
    
    def transform_recouvrements_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transformer les données de recouvrement"""
        try:
            logger.info("🔄 Transformation des données de recouvrement...")
            
            df = df.copy()
            
            # Standardisation des types d'actions
            type_mapping = {
                'relance_amiable': 'RELANCE_AMIABLE',
                'mise_en_demeure': 'MISE_EN_DEMEURE',
                'procedure_judiciaire': 'PROCEDURE_JUDICIAIRE'
            }
            df['type_action'] = df['type_action'].str.lower().map(type_mapping).fillna(df['type_action'].str.upper())
            
            # Standardisation des statuts
            statut_mapping = {
                'en_cours': 'EN_COURS',
                'reussi': 'REUSSI',
                'echec': 'ECHEC',
                'abandonne': 'ABANDONNE'
            }
            df['statut_recouvrement'] = df['statut_recouvrement'].str.lower().map(statut_mapping).fillna(df['statut_recouvrement'].str.upper())
            
            # Standardisation des modes de paiement
            mode_mapping = {
                'espece': 'ESPECE',
                'virement': 'VIREMENT',
                'cheque': 'CHEQUE'
            }
            df['mode_paiement'] = df['mode_paiement'].str.lower().map(mode_mapping).fillna(df['mode_paiement'].str.upper())
            
            # Conversion des montants
            df['montant_paiement'] = pd.to_numeric(df['montant_paiement'], errors='coerce').fillna(0)
            
            # Conversion des dates
            date_columns = ['date_action', 'date_creation', 'date_modification']
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Validation
            df = df.dropna(subset=['recouvrement_id', 'collecte_id'])
            
            logger.info(f"✅ {len(df)} actions de recouvrement transformées")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur transformation recouvrements: {e}")
            return pd.DataFrame()
    
    def load_data_to_staging(self, df: pd.DataFrame, table_name: str) -> bool:
        """Charger les données dans le staging"""
        try:
            if df.empty:
                logger.warning(f"⚠️ Aucune donnée à charger pour {table_name}")
                return True
            
            # Vider d'abord la table staging pour éviter les doublons
            with self.dwh_engine.begin() as conn:
                conn.execute(text(f"DELETE FROM staging.{table_name}"))
            
            logger.info(f"📤 Chargement de {len(df)} enregistrements dans staging.{table_name}")
            
            # Charger les nouvelles données
            df.to_sql(
                name=table_name,
                con=self.dwh_engine,
                schema='staging',
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"✅ Données chargées dans staging.{table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement {table_name}: {e}")
            return False
    
    def create_staging_tables(self):
        """Créer les tables staging si elles n'existent pas"""
        create_tables_sql = """
        -- Création du schéma staging s'il n'existe pas
        CREATE SCHEMA IF NOT EXISTS staging;
        
        -- Table staging pour les collectes
        CREATE TABLE IF NOT EXISTS staging.collectes (
            collecte_id INTEGER PRIMARY KEY,
            reference VARCHAR(100),
            type_collecte VARCHAR(50),
            montant_a_collecter NUMERIC(15,2),
            montant_collecte NUMERIC(15,2),
            statut_collecte VARCHAR(50),
            date_creation DATE,
            date_echeance DATE,
            date_recouvrement DATE,
            agent_collecteur_id INTEGER,
            entreprise_id INTEGER,
            lot_id INTEGER,
            zone_id INTEGER,
            demande_attribution_id INTEGER,
            observations TEXT,
            date_modification TIMESTAMP,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Table staging pour les agents collecteurs
        CREATE TABLE IF NOT EXISTS staging.agents_collecteurs (
            agent_id INTEGER PRIMARY KEY,
            nom_agent VARCHAR(200),
            matricule VARCHAR(50),
            fonction VARCHAR(100),
            zone_affectation_id INTEGER,
            telephone VARCHAR(20),
            email VARCHAR(100),
            statut_agent VARCHAR(20),
            date_embauche DATE,
            date_creation DATE,
            date_modification TIMESTAMP,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Table staging pour les recouvrements
        CREATE TABLE IF NOT EXISTS staging.recouvrements (
            recouvrement_id INTEGER PRIMARY KEY,
            collecte_id INTEGER,
            type_action VARCHAR(50),
            date_action DATE,
            montant_paiement NUMERIC(15,2),
            mode_paiement VARCHAR(20),
            agent_recouvrement_id INTEGER,
            statut_recouvrement VARCHAR(20),
            observations TEXT,
            piece_justificative VARCHAR(200),
            date_creation DATE,
            date_modification TIMESTAMP,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Index pour optimiser les performances
        CREATE INDEX IF NOT EXISTS idx_collectes_agent ON staging.collectes(agent_collecteur_id);
        CREATE INDEX IF NOT EXISTS idx_collectes_entreprise ON staging.collectes(entreprise_id);
        CREATE INDEX IF NOT EXISTS idx_collectes_statut ON staging.collectes(statut_collecte);
        CREATE INDEX IF NOT EXISTS idx_collectes_date_creation ON staging.collectes(date_creation);
        CREATE INDEX IF NOT EXISTS idx_recouvrements_collecte ON staging.recouvrements(collecte_id);
        CREATE INDEX IF NOT EXISTS idx_agents_statut ON staging.agents_collecteurs(statut_agent);
        """
        
        try:
            from sqlalchemy import text
            with self.dwh_engine.begin() as conn:
                conn.execute(text(create_tables_sql))
            logger.info("✅ Tables staging créées/vérifiées")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création tables staging: {e}")
            return False
    
    def run_etl(self):
        """Exécuter l'ETL complet"""
        logger.info("🚀 DÉMARRAGE ETL COLLECTES ET RECOUVREMENTS")
        logger.info("=" * 70)
        
        # Créer les connexions
        if not self.create_connections():
            return False
        
        # Créer les tables staging
        if not self.create_staging_tables():
            return False
        
        success_count = 0
        
        try:
            # ETL Collectes
            logger.info("\n📋 TRAITEMENT DES COLLECTES")
            collectes_df = self.extract_collectes_data()
            if collectes_df is not None:
                collectes_transformed = self.transform_collectes_data(collectes_df)
                if self.load_data_to_staging(collectes_transformed, 'collectes'):
                    success_count += 1
            
            # ETL Agents collecteurs
            logger.info("\n👥 TRAITEMENT DES AGENTS COLLECTEURS")
            agents_df = self.extract_agents_collecteurs_data()
            if agents_df is not None:
                agents_transformed = self.transform_agents_data(agents_df)
                if self.load_data_to_staging(agents_transformed, 'agents_collecteurs'):
                    success_count += 1
            
            # ETL Recouvrements
            logger.info("\n💰 TRAITEMENT DES RECOUVREMENTS")
            recouvrements_df = self.extract_recouvrements_data()
            if recouvrements_df is not None:
                recouvrements_transformed = self.transform_recouvrements_data(recouvrements_df)
                if self.load_data_to_staging(recouvrements_transformed, 'recouvrements'):
                    success_count += 1
            
            logger.info(f"\n📊 RÉSULTATS ETL:")
            logger.info(f"   ✅ Processus réussis: {success_count}/3")
            
            if success_count == 3:
                logger.info("🎉 ETL COLLECTES TERMINÉ AVEC SUCCÈS!")
                return True
            else:
                logger.warning("⚠️ ETL partiellement réussi")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur durant l'ETL: {e}")
            return False
        
        finally:
            # Fermer les connexions
            if self.source_engine:
                self.source_engine.dispose()
            if self.dwh_engine:
                self.dwh_engine.dispose()

def main():
    """Fonction principale"""
    etl = ETLCollectesRecouvrements()
    success = etl.run_etl()
    
    if success:
        print("\n✅ ETL des collectes et recouvrements terminé avec succès")
        print("💡 Prochaines étapes:")
        print("   1. Exécuter les modèles dbt pour transformer les données staging")
        print("   2. Déployer les vues KPI")
        print("   3. Valider les données et les indicateurs")
    else:
        print("\n❌ ETL des collectes et recouvrements échoué")
        print("🔍 Vérifiez les logs pour plus de détails")

if __name__ == "__main__":
    main()