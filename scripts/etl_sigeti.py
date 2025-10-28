"""
Script de synchronisation des données SIGETI
Copie les données de la base SIGETI source vers le data warehouse
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from datetime import datetime

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des bases de données
SOURCE_CONFIG = {
    'host': 'host.docker.internal',
    'port': '5432',
    'database': 'sigeti_node_db',
    'username': 'postgres',
    'password': 'postgres'
}

TARGET_CONFIG = {
    'host': 'host.docker.internal',
    'port': '5432',
    'database': 'sigeti_dwh',
    'username': 'sigeti_user',
    'password': 'sigeti123'
}

def create_connection(config):
    """Crée une connexion SQLAlchemy"""
    connection_string = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?client_encoding=utf8"
    return create_engine(connection_string)

def extract_transform_load_table(source_engine, target_engine, table_name, transform_query=None):
    """
    Extrait, transforme et charge une table
    """
    try:
        logger.info(f"Début de l'ETL pour la table: {table_name}")
        
        # Query par défaut ou personnalisée
        if transform_query is None:
            query = f"SELECT * FROM {table_name}"
        else:
            query = transform_query
        
        # Extraction
        logger.info(f"Extraction des données de {table_name}...")
        df = pd.read_sql(query, source_engine)
        logger.info(f"Nombre de lignes extraites: {len(df)}")
        
        # Chargement
        logger.info(f"Chargement vers staging.{table_name}...")
        
        # Vider la table si elle existe au lieu de la supprimer
        with target_engine.begin() as conn:
            try:
                # Essayer de truncate la table si elle existe
                conn.execute(text(f"TRUNCATE TABLE staging.{table_name} RESTART IDENTITY CASCADE"))
                logger.info(f"Table staging.{table_name} vidée")
                # Insérer les nouvelles données
                df.to_sql(table_name, conn, schema='staging', if_exists='append', index=False)
            except Exception as e:
                # Si la table n'existe pas, la créer
                logger.info(f"Création de la table staging.{table_name} (première fois)")
                df.to_sql(table_name, conn, schema='staging', if_exists='replace', index=False)
                
        logger.info(f"Chargement terminé pour {table_name}")
        
        return len(df)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ETL de {table_name}: {str(e)}")
        raise

def main():
    """Fonction principale d'ETL"""
    
    # Création des connexions
    logger.info("Connexion aux bases de données...")
    source_engine = create_connection(SOURCE_CONFIG)
    target_engine = create_connection(TARGET_CONFIG)
    
    # Créer le schéma staging s'il n'existe pas
    with target_engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging;"))
    
    # Définition des requêtes de transformation
    queries = {
        'demandes_attribution': """
            SELECT 
                id as demande_id,
                reference,
                statut::text as statut,
                etape_courante,
                type_demande::text as type_demande,
                operateur_id,
                entreprise_id,
                lot_id,
                zone_id,
                priorite,
                (financement->>'montantTotal')::numeric as montant_financement,
                (emplois->>'total')::int as nombre_emplois_total,
                CASE 
                    WHEN lower(priorite) IN ('haute', 'élevée', 'prioritaire', 'urgente') 
                    THEN true 
                    ELSE false 
                END as est_prioritaire,
                created_at as date_creation,
                updated_at as date_modification,
                CASE 
                    WHEN statut::text IN ('ACCEPTEE', 'REJETEE') 
                    THEN extract(days from (updated_at - created_at))
                    WHEN statut::text = 'EN_COURS' 
                    THEN extract(days from (current_timestamp - created_at))
                    ELSE null
                END as delai_traitement_jours,
                CASE 
                    WHEN statut::text IN ('ACCEPTEE', 'REJETEE') THEN true 
                    ELSE false 
                END as est_finalisee,
                CASE 
                    WHEN statut::text = 'ACCEPTEE' THEN true 
                    ELSE false 
                END as est_acceptee
            FROM demandes_attribution
        """,
        
        'entreprises': """
            SELECT 
                id as entreprise_id,
                raison_sociale,
                telephone,
                email,
                registre_commerce,
                compte_contribuable,
                forme_juridique,
                adresse,
                date_constitution,
                domaine_activite_id,
                date_creation,
                date_modification
            FROM entreprises
        """,
        
        'lots': """
            SELECT 
                id as lot_id,
                numero as numero_lot,
                ilot,
                superficie,
                unite_mesure,
                REPLACE(prix::text, '€', 'EUR')::numeric as prix,
                statut::text as statut,
                priorite,
                viabilite,
                COALESCE(description, '') as description,
                coordonnees,
                zone_industrielle_id,
                entreprise_id,
                operateur_id,
                date_acquisition,
                date_reservation,
                delai_option,
                created_at as date_creation,
                updated_at as date_modification
            FROM lots
        """,
        
        'zones_industrielles': """
            SELECT 
                id as zone_id,
                code as code_zone,
                libelle,
                COALESCE(description, '') as description,
                superficie,
                unite_mesure::text as unite_mesure,
                lots_disponibles,
                COALESCE(adresse, '') as adresse,
                statut::text as statut,
                created_at as date_creation,
                updated_at as date_modification
            FROM zones_industrielles
        """
    }
    
    # Exécution de l'ETL pour chaque table
    total_rows = 0
    for table_name, query in queries.items():
        try:
            rows_processed = extract_transform_load_table(source_engine, target_engine, table_name, query)
            total_rows += rows_processed
        except Exception as e:
            logger.error(f"Échec de l'ETL pour {table_name}: {str(e)}")
            continue
    
    logger.info(f"ETL terminé avec succès. Total de lignes traitées: {total_rows}")

if __name__ == "__main__":
    main()