"""
Script ETL SIGETI avec PySpark
Extraction, transformation et chargement des données SIGETI vers le data warehouse
Utilise Apache Spark pour des performances optimales et une meilleure gestion des données
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lower, regexp_replace, current_timestamp, lit, to_timestamp, datediff
from pyspark.sql.types import *
import logging
from datetime import datetime
import os

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des bases de données
SOURCE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'sigeti_node_db',
    'user': 'postgres',
    'password': 'postgres',
    'driver': 'org.postgresql.Driver'
}

TARGET_CONFIG = {
    'host': 'localhost', 
    'port': '5432',
    'database': 'sigeti_dwh',
    'user': 'postgres',
    'password': 'postgres',
    'driver': 'org.postgresql.Driver'
}

def create_spark_session():
    """Crée une session Spark avec configuration PostgreSQL"""
    
    # Chemin vers le driver PostgreSQL
    jar_path = os.path.join(os.getcwd(), "spark_jars", "postgresql-42.7.4.jar")
    
    spark = SparkSession.builder \
        .appName("SIGETI_ETL") \
        .config("spark.driver.extraClassPath", jar_path) \
        .config("spark.executor.extraClassPath", jar_path) \
        .config("spark.jars", jar_path) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()
    
    # Réduire le niveau de log pour éviter le spam
    spark.sparkContext.setLogLevel("WARN")
    
    return spark

def get_jdbc_url(config):
    """Génère l'URL JDBC PostgreSQL"""
    return f"jdbc:postgresql://{config['host']}:{config['port']}/{config['database']}"

def read_postgres_table(spark, config, table_name, query=None):
    """Lit une table ou exécute une requête depuis PostgreSQL"""
    
    jdbc_url = get_jdbc_url(config)
    
    if query:
        # Exécuter une requête personnalisée
        df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("query", query) \
            .option("user", config['user']) \
            .option("password", config['password']) \
            .option("driver", config['driver']) \
            .option("encoding", "UTF-8") \
            .load()
    else:
        # Lire une table complète
        df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", table_name) \
            .option("user", config['user']) \
            .option("password", config['password']) \
            .option("driver", config['driver']) \
            .option("encoding", "UTF-8") \
            .load()
    
    return df

def write_postgres_table(df, config, table_name, schema="staging"):
    """Écrit un DataFrame vers PostgreSQL"""
    
    jdbc_url = get_jdbc_url(config)
    
    df.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"{schema}.{table_name}") \
        .option("user", config['user']) \
        .option("password", config['password']) \
        .option("driver", config['driver']) \
        .mode("overwrite") \
        .save()

def transform_demandes_attribution(df):
    """Transformations spécifiques pour les demandes d'attribution"""
    
    logger.info("Transformation des demandes d'attribution...")
    
    # Création des colonnes calculées
    df_transformed = df \
        .withColumnRenamed("id", "demande_id") \
        .withColumn("statut", col("statut").cast("string")) \
        .withColumn("type_demande", col("type_demande").cast("string")) \
        .withColumn("montant_financement", 
                   col("financement").getItem("montantTotal").cast("decimal(15,2)")) \
        .withColumn("nombre_emplois_total", 
                   col("emplois").getItem("total").cast("integer")) \
        .withColumn("est_prioritaire",
                   when(lower(col("priorite")).isin(['haute', 'élevée', 'prioritaire', 'urgente']), 
                        lit(True)).otherwise(lit(False))) \
        .withColumnRenamed("created_at", "date_creation") \
        .withColumnRenamed("updated_at", "date_modification") \
        .withColumn("delai_traitement_jours",
                   when(col("statut").isin(['ACCEPTEE', 'REJETEE']),
                        datediff(col("date_modification"), col("date_creation")))
                   .when(col("statut") == 'EN_COURS',
                         datediff(current_timestamp(), col("date_creation")))
                   .otherwise(lit(None))) \
        .withColumn("est_finalisee",
                   when(col("statut").isin(['ACCEPTEE', 'REJETEE']), lit(True))
                   .otherwise(lit(False))) \
        .withColumn("est_acceptee",
                   when(col("statut") == 'ACCEPTEE', lit(True))
                   .otherwise(lit(False)))
    
    # Sélection des colonnes finales
    final_columns = [
        "demande_id", "reference", "statut", "etape_courante", "type_demande",
        "operateur_id", "entreprise_id", "lot_id", "zone_id", "priorite",
        "montant_financement", "nombre_emplois_total", "est_prioritaire",
        "date_creation", "date_modification", "delai_traitement_jours",
        "est_finalisee", "est_acceptee"
    ]
    
    return df_transformed.select(*final_columns)

def transform_entreprises(df):
    """Transformations spécifiques pour les entreprises"""
    
    logger.info("Transformation des entreprises...")
    
    return df \
        .withColumnRenamed("id", "entreprise_id") \
        .select("entreprise_id", "raison_sociale", "telephone", "email", 
               "registre_commerce", "compte_contribuable", "forme_juridique", 
               "adresse", "date_constitution", "domaine_activite_id",
               "date_creation", "date_modification")

def transform_lots(df):
    """Transformations spécifiques pour les lots"""
    
    logger.info("Transformation des lots...")
    
    return df \
        .withColumnRenamed("id", "lot_id") \
        .withColumnRenamed("numero", "numero_lot") \
        .withColumn("statut", col("statut").cast("string")) \
        .withColumnRenamed("created_at", "date_creation") \
        .withColumnRenamed("updated_at", "date_modification") \
        .select("lot_id", "numero_lot", "ilot", "superficie", "unite_mesure", 
               "prix", "statut", "priorite", "viabilite", "description", 
               "coordonnees", "zone_industrielle_id", "entreprise_id", 
               "operateur_id", "date_acquisition", "date_reservation", 
               "delai_option", "date_creation", "date_modification")

def transform_zones_industrielles(df):
    """Transformations spécifiques pour les zones industrielles"""
    
    logger.info("Transformation des zones industrielles...")
    
    return df \
        .withColumnRenamed("id", "zone_id") \
        .withColumnRenamed("code", "code_zone") \
        .withColumn("unite_mesure", col("unite_mesure").cast("string")) \
        .withColumn("statut", col("statut").cast("string")) \
        .withColumnRenamed("created_at", "date_creation") \
        .withColumnRenamed("updated_at", "date_modification") \
        .select("zone_id", "code_zone", "libelle", "description", 
               "superficie", "unite_mesure", "lots_disponibles", 
               "adresse", "statut", "date_creation", "date_modification")

def create_staging_schema(spark, target_config):
    """Crée le schéma staging s'il n'existe pas"""
    
    logger.info("Création du schéma staging...")
    
    # Créer une connexion pour exécuter du DDL
    jdbc_url = get_jdbc_url(target_config)
    
    # Utiliser une requête vide pour établir la connexion et créer le schéma
    try:
        temp_df = spark.sql("SELECT 1 as dummy")
        temp_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", "staging.temp_table") \
            .option("user", target_config['user']) \
            .option("password", target_config['password']) \
            .option("driver", target_config['driver']) \
            .option("createTableColumnTypes", "dummy INTEGER") \
            .mode("overwrite") \
            .save()
        
        # Supprimer la table temporaire
        temp_df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("query", "DROP TABLE IF EXISTS staging.temp_table") \
            .option("user", target_config['user']) \
            .option("password", target_config['password']) \
            .option("driver", target_config['driver']) \
            .load()
            
    except Exception as e:
        logger.info(f"Le schéma staging existe probablement déjà: {str(e)}")

def main():
    """Fonction principale d'ETL avec PySpark"""
    
    logger.info("Démarrage de l'ETL SIGETI avec PySpark...")
    
    # Créer la session Spark
    spark = create_spark_session()
    logger.info("Session Spark créée avec succès")
    
    try:
        # Créer le schéma staging
        create_staging_schema(spark, TARGET_CONFIG)
        
        # Configuration des tables à traiter
        tables_config = {
            'demandes_attribution': {
                'transform_func': transform_demandes_attribution
            },
            'entreprises': {
                'transform_func': transform_entreprises
            },
            'lots': {
                'transform_func': transform_lots
            },
            'zones_industrielles': {
                'transform_func': transform_zones_industrielles
            }
        }
        
        total_rows = 0
        
        # Traiter chaque table
        for table_name, config in tables_config.items():
            try:
                logger.info(f"Traitement de la table: {table_name}")
                
                # Extraction
                df = read_postgres_table(spark, SOURCE_CONFIG, table_name)
                row_count = df.count()
                logger.info(f"Nombre de lignes extraites de {table_name}: {row_count}")
                
                # Transformation
                df_transformed = config['transform_func'](df)
                
                # Chargement
                write_postgres_table(df_transformed, TARGET_CONFIG, table_name, "staging")
                logger.info(f"Chargement terminé pour {table_name}")
                
                total_rows += row_count
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {table_name}: {str(e)}")
                continue
        
        logger.info(f"ETL terminé avec succès. Total de lignes traitées: {total_rows}")
        
    except Exception as e:
        logger.error(f"Erreur générale dans l'ETL: {str(e)}")
        raise
    
    finally:
        # Fermer la session Spark
        spark.stop()
        logger.info("Session Spark fermée")

if __name__ == "__main__":
    main()