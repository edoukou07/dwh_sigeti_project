#!/usr/bin/env python3
"""
ETL STAGING VERS MODÈLE DIMENSIONNEL - COLLECTES SIGETI
Script pour transformer les données du staging vers les dimensions et faits
Architecture: Staging → Dimensions → Faits
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import os
import hashlib
from typing import Dict, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_staging_to_dimensional.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ETLStagingToDimensional:
    """ETL pour alimenter le modèle dimensionnel depuis le staging"""
    
    def __init__(self):
        self.dwh_engine = None
        self.batch_id = f"ETL_DIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_connection(self) -> bool:
        """Créer la connexion à la base DWH"""
        try:
            # Configuration DWH
            dwh_config = {
                'host': os.getenv('DWH_HOST', 'localhost'),
                'port': int(os.getenv('DWH_PORT', 5432)),
                'database': os.getenv('DWH_DATABASE', 'sigeti_dwh'),
                'user': os.getenv('DWH_USER', 'sigeti_user'),
                'password': os.getenv('DWH_PASSWORD', 'sigeti123')
            }
            
            self.dwh_engine = create_engine(
                f"postgresql://{dwh_config['user']}:{dwh_config['password']}@"
                f"{dwh_config['host']}:{dwh_config['port']}/{dwh_config['database']}"
            )
            
            # Test de connexion
            with self.dwh_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Connexion DWH établie")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion DWH: {e}")
            return False
    
    def generate_key(self, prefix: str, natural_key: str, version: str = "1") -> str:
        """Générer une clé surrogate"""
        key_input = f"{prefix}_{natural_key}_{version}"
        hash_obj = hashlib.md5(key_input.encode())
        return f"{prefix}_{hash_obj.hexdigest()[:8].upper()}"
    
    def get_date_key(self, date_value) -> Optional[int]:
        """Obtenir la clé de dimension date"""
        if pd.isna(date_value) or date_value is None:
            return None
        
        try:
            if isinstance(date_value, str):
                date_obj = pd.to_datetime(date_value).date()
            else:
                date_obj = date_value.date() if hasattr(date_value, 'date') else date_value
            
            # Format YYYYMMDD pour la clé
            return int(date_obj.strftime('%Y%m%d'))
        except:
            return None
    
    def load_dim_agents_collecteurs(self) -> bool:
        """Charger la dimension agents collecteurs depuis staging"""
        try:
            logger.info("📥 Chargement dim_agents_collecteurs...")
            
            with self.dwh_engine.connect() as conn:
                # Extraire les agents du staging
                query = """
                SELECT DISTINCT
                    agent_id,
                    nom_agent,
                    matricule,
                    fonction,
                    zone_affectation_id,
                    telephone,
                    email,
                    statut_agent,
                    date_embauche,
                    date_creation,
                    date_modification
                FROM staging.agents_collecteurs
                """
                
                df_agents = pd.read_sql(query, conn)
                
                if df_agents.empty:
                    logger.warning("⚠️ Aucun agent à traiter")
                    return True
                
                # Transformer et créer les clés surrogate
                df_agents['agent_key'] = df_agents.apply(
                    lambda row: self.generate_key('AGT', str(row['agent_id'])), axis=1
                )
                
                # Séparer nom et prénom si nécessaire
                df_agents['nom_complet'] = df_agents['nom_agent']
                df_agents['prenom_agent'] = ''  # À adapter selon les données
                
                # SCD Type 2: Vérifier les changements
                existing_query = """
                SELECT agent_id, agent_key, nom_agent, statut_agent, version_courante
                FROM public.dim_agents_collecteurs
                WHERE version_courante = true
                """
                
                df_existing = pd.read_sql(existing_query, conn)
                
                # Upsert logic - ici simplifié pour insert/update
                for _, row in df_agents.iterrows():
                    # Vérifier si l'agent existe déjà
                    existing_agent = df_existing[df_existing['agent_id'] == row['agent_id']]
                    
                    if existing_agent.empty:
                        # Nouvel agent - INSERT
                        insert_query = text("""
                            INSERT INTO public.dim_agents_collecteurs (
                                agent_key, agent_id, nom_agent, prenom_agent, nom_complet,
                                matricule, fonction, telephone, email, statut_agent,
                                zone_affectation_id, date_embauche, date_creation, date_modification,
                                date_debut_validite, date_fin_validite, version_courante
                            ) VALUES (
                                :agent_key, :agent_id, :nom_agent, :prenom_agent, :nom_complet,
                                :matricule, :fonction, :telephone, :email, :statut_agent,
                                :zone_affectation_id, :date_embauche, :date_creation, :date_modification,
                                CURRENT_TIMESTAMP, '9999-12-31 23:59:59', true
                            ) ON CONFLICT (agent_key) DO NOTHING
                        """)
                        
                        conn.execute(insert_query, {
                            'agent_key': row['agent_key'],
                            'agent_id': row['agent_id'],
                            'nom_agent': row['nom_agent'],
                            'prenom_agent': row['prenom_agent'],
                            'nom_complet': row['nom_complet'],
                            'matricule': row['matricule'],
                            'fonction': row['fonction'],
                            'telephone': row['telephone'],
                            'email': row['email'],
                            'statut_agent': row['statut_agent'],
                            'zone_affectation_id': row['zone_affectation_id'],
                            'date_embauche': row['date_embauche'],
                            'date_creation': row['date_creation'],
                            'date_modification': row['date_modification']
                        })
                    
                conn.commit()
                logger.info(f"✅ {len(df_agents)} agents traités")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur chargement agents: {e}")
            return False
    
    def load_fct_collectes(self) -> bool:
        """Charger la table de fait collectes"""
        try:
            logger.info("📥 Chargement fct_collectes...")
            
            with self.dwh_engine.connect() as conn:
                # Extraire les collectes avec jointures pour obtenir les clés
                query = """
                SELECT 
                    c.collecte_id,
                    c.reference,
                    c.type_collecte,
                    c.montant_a_collecter,
                    c.montant_collecte,
                    c.statut_collecte,
                    c.date_creation,
                    c.date_echeance,
                    c.date_recouvrement,
                    c.date_modification,
                    c.agent_collecteur_id,
                    c.entreprise_id,
                    c.lot_id,
                    c.zone_id,
                    c.demande_attribution_id,
                    c.observations
                FROM staging.collectes c
                """
                
                df_collectes = pd.read_sql(query, conn)
                
                if df_collectes.empty:
                    logger.warning("⚠️ Aucune collecte à traiter")
                    return True
                
                # Transformer les données pour le fait
                for _, row in df_collectes.iterrows():
                    # Calculs dérivés
                    montant_a_collecter = row['montant_a_collecter'] or 0
                    montant_collecte = row['montant_collecte'] or 0
                    montant_restant = montant_a_collecter - montant_collecte
                    taux_recouvrement = (montant_collecte / montant_a_collecter) if montant_a_collecter > 0 else 0
                    
                    # Calcul du délai
                    delai_jours = None
                    if row['date_recouvrement'] and row['date_creation']:
                        date_creation = pd.to_datetime(row['date_creation'])
                        date_recouvrement = pd.to_datetime(row['date_recouvrement'])
                        delai_jours = (date_recouvrement - date_creation).days
                    
                    # Clés vers dimensions
                    agent_key = None
                    if row['agent_collecteur_id']:
                        agent_key = self.generate_key('AGT', str(row['agent_collecteur_id']))
                    
                    type_collecte_key = None
                    if row['type_collecte']:
                        type_collecte_key = f"TYP_{row['type_collecte']}"
                    
                    statut_key = None
                    if row['statut_collecte']:
                        statut_key = f"STAT_{row['statut_collecte']}"
                    
                    # Clés de dates
                    date_creation_key = self.get_date_key(row['date_creation'])
                    date_echeance_key = self.get_date_key(row['date_echeance'])
                    date_recouvrement_key = self.get_date_key(row['date_recouvrement'])
                    date_modification_key = self.get_date_key(row['date_modification'])
                    
                    # Insert dans fct_collectes
                    insert_fact = text("""
                        INSERT INTO public.fct_collectes (
                            collecte_id, date_creation_key, date_echeance_key, 
                            date_recouvrement_key, date_modification_key,
                            agent_collecteur_key, type_collecte_key, statut_collecte_key,
                            montant_a_collecter, montant_collecte, montant_restant_du,
                            taux_recouvrement, delai_recouvrement_jours,
                            reference, observations, demande_attribution_id,
                            etl_batch_id
                        ) VALUES (
                            :collecte_id, :date_creation_key, :date_echeance_key,
                            :date_recouvrement_key, :date_modification_key,
                            :agent_collecteur_key, :type_collecte_key, :statut_collecte_key,
                            :montant_a_collecter, :montant_collecte, :montant_restant_du,
                            :taux_recouvrement, :delai_recouvrement_jours,
                            :reference, :observations, :demande_attribution_id,
                            :etl_batch_id
                        ) ON CONFLICT (collecte_id) DO UPDATE SET
                            montant_collecte = EXCLUDED.montant_collecte,
                            montant_restant_du = EXCLUDED.montant_restant_du,
                            taux_recouvrement = EXCLUDED.taux_recouvrement,
                            statut_collecte_key = EXCLUDED.statut_collecte_key,
                            date_modification_key = EXCLUDED.date_modification_key,
                            etl_batch_id = EXCLUDED.etl_batch_id
                    """)
                    
                    conn.execute(insert_fact, {
                        'collecte_id': row['collecte_id'],
                        'date_creation_key': date_creation_key,
                        'date_echeance_key': date_echeance_key,
                        'date_recouvrement_key': date_recouvrement_key,
                        'date_modification_key': date_modification_key,
                        'agent_collecteur_key': agent_key,
                        'type_collecte_key': type_collecte_key,
                        'statut_collecte_key': statut_key,
                        'montant_a_collecter': montant_a_collecter,
                        'montant_collecte': montant_collecte,
                        'montant_restant_du': montant_restant,
                        'taux_recouvrement': taux_recouvrement,
                        'delai_recouvrement_jours': delai_jours,
                        'reference': row['reference'],
                        'observations': row['observations'],
                        'demande_attribution_id': row['demande_attribution_id'],
                        'etl_batch_id': self.batch_id
                    })
                
                conn.commit()
                logger.info(f"✅ {len(df_collectes)} collectes traitées")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur chargement collectes: {e}")
            return False
    
    def load_fct_recouvrements(self) -> bool:
        """Charger la table de fait recouvrements"""
        try:
            logger.info("📥 Chargement fct_recouvrements...")
            
            with self.dwh_engine.connect() as conn:
                query = """
                SELECT 
                    r.recouvrement_id,
                    r.collecte_id,
                    r.type_action,
                    r.date_action,
                    r.montant_paiement,
                    r.mode_paiement,
                    r.agent_recouvrement_id,
                    r.statut_recouvrement,
                    r.observations,
                    r.piece_justificative,
                    r.date_creation,
                    r.date_modification
                FROM staging.recouvrements r
                """
                
                df_recouvrements = pd.read_sql(query, conn)
                
                if df_recouvrements.empty:
                    logger.warning("⚠️ Aucun recouvrement à traiter")
                    return True
                
                for _, row in df_recouvrements.iterrows():
                    # Obtenir la clé du fait collecte
                    collecte_fact_key = None
                    if row['collecte_id']:
                        fact_query = text("SELECT collecte_fact_key FROM public.fct_collectes WHERE collecte_id = :collecte_id")
                        result = conn.execute(fact_query, {'collecte_id': row['collecte_id']}).fetchone()
                        if result:
                            collecte_fact_key = result[0]
                    
                    # Clés vers dimensions
                    agent_key = None
                    if row['agent_recouvrement_id']:
                        agent_key = self.generate_key('AGT', str(row['agent_recouvrement_id']))
                    
                    # Clés de dates
                    date_action_key = self.get_date_key(row['date_action'])
                    date_creation_key = self.get_date_key(row['date_creation'])
                    date_modification_key = self.get_date_key(row['date_modification'])
                    
                    montant_paiement = row['montant_paiement'] or 0
                    
                    insert_fact = text("""
                        INSERT INTO public.fct_recouvrements (
                            recouvrement_id, collecte_fact_key, collecte_id,
                            date_action_key, date_creation_key, date_modification_key,
                            agent_recouvrement_key, montant_paiement, montant_net,
                            type_action, mode_paiement, statut_recouvrement,
                            observations, piece_justificative, etl_batch_id
                        ) VALUES (
                            :recouvrement_id, :collecte_fact_key, :collecte_id,
                            :date_action_key, :date_creation_key, :date_modification_key,
                            :agent_recouvrement_key, :montant_paiement, :montant_net,
                            :type_action, :mode_paiement, :statut_recouvrement,
                            :observations, :piece_justificative, :etl_batch_id
                        ) ON CONFLICT (recouvrement_id) DO UPDATE SET
                            montant_paiement = EXCLUDED.montant_paiement,
                            montant_net = EXCLUDED.montant_net,
                            statut_recouvrement = EXCLUDED.statut_recouvrement,
                            etl_batch_id = EXCLUDED.etl_batch_id
                    """)
                    
                    conn.execute(insert_fact, {
                        'recouvrement_id': row['recouvrement_id'],
                        'collecte_fact_key': collecte_fact_key,
                        'collecte_id': row['collecte_id'],
                        'date_action_key': date_action_key,
                        'date_creation_key': date_creation_key,
                        'date_modification_key': date_modification_key,
                        'agent_recouvrement_key': agent_key,
                        'montant_paiement': montant_paiement,
                        'montant_net': montant_paiement,  # Simplifié
                        'type_action': row['type_action'],
                        'mode_paiement': row['mode_paiement'],
                        'statut_recouvrement': row['statut_recouvrement'],
                        'observations': row['observations'],
                        'piece_justificative': row['piece_justificative'],
                        'etl_batch_id': self.batch_id
                    })
                
                conn.commit()
                logger.info(f"✅ {len(df_recouvrements)} recouvrements traités")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur chargement recouvrements: {e}")
            return False
    
    def run_etl(self) -> bool:
        """Exécuter l'ETL complet staging vers dimensionnel"""
        logger.info("🚀 DÉMARRAGE ETL STAGING → DIMENSIONNEL")
        logger.info(f"📋 Batch ID: {self.batch_id}")
        logger.info("=" * 60)
        
        if not self.create_connection():
            return False
        
        success_count = 0
        total_steps = 3
        
        try:
            # 1. Charger dimensions
            if self.load_dim_agents_collecteurs():
                success_count += 1
            
            # 2. Charger fait collectes
            if self.load_fct_collectes():
                success_count += 1
            
            # 3. Charger fait recouvrements
            if self.load_fct_recouvrements():
                success_count += 1
            
            logger.info(f"\n📊 RÉSULTATS ETL:")
            logger.info(f"   ✅ Processus réussis: {success_count}/{total_steps}")
            
            if success_count == total_steps:
                logger.info("🎉 ETL DIMENSIONNEL TERMINÉ AVEC SUCCÈS!")
                return True
            else:
                logger.warning("⚠️ ETL partiellement réussi")
                return False
        
        except Exception as e:
            logger.error(f"❌ Erreur durant l'ETL: {e}")
            return False
        
        finally:
            if self.dwh_engine:
                self.dwh_engine.dispose()

def main():
    """Fonction principale"""
    etl = ETLStagingToDimensional()
    success = etl.run_etl()
    
    if success:
        print("\n✅ ETL staging vers dimensionnel terminé avec succès")
        print("💡 Prochaines étapes:")
        print("   1. Valider les données dans les tables de faits")
        print("   2. Recréer les KPI basés sur le modèle dimensionnel")
        print("   3. Tester les performances des nouvelles vues")
    else:
        print("\n❌ ETL staging vers dimensionnel échoué")
        print("🔍 Vérifiez les logs pour plus de détails")

if __name__ == "__main__":
    main()