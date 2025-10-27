"""
Script Python pour créer et déployer les vues KPI SIGETI
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os
from datetime import datetime

# Configuration de la base de données
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sigeti_dwh',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

# Définition des vues KPI
VIEWS_SQL = {
    # KPI 1: Nombre de demandes par statut
    'v_kpi_demandes_par_statut': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_statut AS
        SELECT 
            'Demandes par statut' as indicateur,
            s.nom as statut,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT f.demande_id) * 100.0 / SUM(COUNT(DISTINCT f.demande_id)) OVER(), 2) as pourcentage,
            CURRENT_DATE as date_calcul,
            'Répartition des demandes selon leur statut de traitement' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_statuts_demandes s ON f.statut_key = s.statut_key
        GROUP BY s.nom
        ORDER BY nombre_demandes DESC;
    """,

    # KPI 2: Nombre de demandes par type (zone vs hors zone)
    'v_kpi_demandes_par_type': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_type AS
        SELECT 
            'Demandes par type de zone' as indicateur,
            CASE 
                WHEN SUM(nb_demandes_zone_industrielle) > 0 THEN 'ZONE_INDUSTRIELLE'
                ELSE 'HORS_ZONE_INDUSTRIELLE'
            END as type_zone,
            COUNT(DISTINCT demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT demande_id) * 100.0 / SUM(COUNT(DISTINCT demande_id)) OVER(), 2) as pourcentage,
            SUM(montant_financement) as montant_total,
            SUM(nombre_emplois) as emplois_total,
            CURRENT_DATE as date_calcul,
            'Répartition entre demandes en zone industrielle et hors zone' as interpretation
        FROM marts.fct_demandes_attribution
        GROUP BY 
            CASE 
                WHEN SUM(nb_demandes_zone_industrielle) > 0 THEN 'ZONE_INDUSTRIELLE'
                ELSE 'HORS_ZONE_INDUSTRIELLE'
            END
        ORDER BY nombre_demandes DESC;
    """,

    # KPI 3: Nombre de demandes par zone, lot et entreprise
    'v_kpi_demandes_par_entite': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_entite AS
        SELECT 
            'Demandes par entité' as indicateur,
            z.nom as zone_industrielle,
            l.nom as lot,
            e.raison_sociale as entreprise,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            SUM(f.montant_financement) as montant_total_finance,
            SUM(f.nombre_emplois) as emplois_crees,
            AVG(f.delai_traitement_jours) as delai_moyen_jours,
            CURRENT_DATE as date_calcul,
            'Analyse détaillée par zone, lot et entreprise' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_zones_industrielles z ON f.zone_key = z.zone_key
        JOIN marts.dim_lots l ON f.lot_key = l.lot_key
        JOIN marts.dim_entreprises e ON f.entreprise_key = e.entreprise_key
        GROUP BY z.nom, l.nom, e.raison_sociale
        ORDER BY nombre_demandes DESC, montant_total_finance DESC;
    """,

    # KPI 4: Demandes prioritaires vs normales
    'v_kpi_demandes_prioritaires': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_prioritaires AS
        SELECT 
            'Demandes prioritaires vs normales' as indicateur,
            CASE 
                WHEN SUM(nb_demandes_prioritaires) > 0 THEN 'PRIORITAIRE'
                ELSE 'NORMALE'
            END as niveau_priorite,
            COUNT(DISTINCT demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT demande_id) * 100.0 / SUM(COUNT(DISTINCT demande_id)) OVER(), 2) as pourcentage,
            SUM(montant_financement) as montant_total,
            AVG(delai_traitement_jours) as delai_moyen_jours,
            CURRENT_DATE as date_calcul,
            'Comparaison entre demandes prioritaires et normales' as interpretation
        FROM marts.fct_demandes_attribution
        GROUP BY 
            CASE 
                WHEN SUM(nb_demandes_prioritaires) > 0 THEN 'PRIORITAIRE'
                ELSE 'NORMALE'
            END
        ORDER BY niveau_priorite DESC;
    """,

    # KPI 5: Délai moyen de traitement
    'v_kpi_delai_traitement': """
        CREATE OR REPLACE VIEW public.v_kpi_delai_traitement AS
        SELECT 
            'Délai de traitement des demandes' as indicateur,
            ROUND(AVG(delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delai_traitement_jours)::numeric, 1) as delai_median_jours,
            MIN(delai_traitement_jours) as delai_min_jours,
            MAX(delai_traitement_jours) as delai_max_jours,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours <= 7 THEN demande_id END) as demandes_sous_7j,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours BETWEEN 8 AND 15 THEN demande_id END) as demandes_8_15j,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours > 15 THEN demande_id END) as demandes_plus_15j,
            COUNT(DISTINCT CASE WHEN nb_demandes_finalisees > 0 THEN demande_id END) as total_demandes_finalisees,
            CURRENT_DATE as date_calcul,
            'Analyse des délais de traitement depuis création jusqu''à validation/rejet' as interpretation
        FROM marts.fct_demandes_attribution
        WHERE delai_traitement_jours IS NOT NULL AND delai_traitement_jours > 0;
    """,

    # KPI 6: Taux d'acceptation/approbation
    'v_kpi_taux_acceptation': """
        CREATE OR REPLACE VIEW public.v_kpi_taux_acceptation AS
        SELECT 
            'Taux d''acceptation des demandes' as indicateur,
            ROUND(
                (SUM(nb_demandes_acceptees) * 100.0) / 
                NULLIF(SUM(nb_demandes_finalisees), 0), 2
            ) as taux_acceptation_pourcentage,
            SUM(nb_demandes_acceptees) as demandes_acceptees,
            SUM(nb_demandes_rejetees) as demandes_rejetees,
            SUM(nb_demandes_en_cours) as demandes_en_cours,
            SUM(nb_demandes_finalisees) as demandes_finalisees,
            COUNT(DISTINCT demande_id) as total_demandes,
            CURRENT_DATE as date_calcul,
            'Ratio des demandes acceptées par rapport aux demandes traitées' as interpretation
        FROM marts.fct_demandes_attribution;
    """,

    # KPI 7: Évolution des demandes prioritaires par période
    'v_kpi_evolution_prioritaires': """
        CREATE OR REPLACE VIEW public.v_kpi_evolution_prioritaires AS
        SELECT 
            'Évolution demandes prioritaires' as indicateur,
            d.annee,
            d.mois,
            d.nom_mois,
            COUNT(DISTINCT f.demande_id) as total_demandes,
            SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
            COUNT(DISTINCT f.demande_id) - SUM(f.nb_demandes_prioritaires) as demandes_normales,
            ROUND(
                (SUM(f.nb_demandes_prioritaires) * 100.0) / 
                NULLIF(COUNT(DISTINCT f.demande_id), 0), 2
            ) as pourcentage_prioritaires,
            SUM(f.montant_financement) as montant_total_mois,
            AVG(f.delai_traitement_jours) as delai_moyen_mois,
            CURRENT_DATE as date_calcul,
            'Évolution temporelle de la proportion de demandes prioritaires' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_date d ON f.date_creation_key = d.date_key
        GROUP BY d.annee, d.mois, d.nom_mois
        ORDER BY d.annee, d.mois;
    """,
    
    'v_kpi_delai_traitement': """
        CREATE OR REPLACE VIEW public.v_kpi_delai_traitement AS
        SELECT 
            'Délai de traitement des demandes' as indicateur,
            ROUND(AVG(delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delai_traitement_jours)::numeric, 1) as delai_median_jours,
            MIN(delai_traitement_jours) as delai_min_jours,
            MAX(delai_traitement_jours) as delai_max_jours,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours <= 7 THEN demande_id END) as demandes_sous_7j,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours BETWEEN 8 AND 15 THEN demande_id END) as demandes_8_15j,
            COUNT(DISTINCT CASE WHEN delai_traitement_jours > 15 THEN demande_id END) as demandes_plus_15j,
            COUNT(DISTINCT CASE WHEN nb_demandes_finalisees > 0 THEN demande_id END) as total_demandes_finalisees,
            CURRENT_DATE as date_calcul,
            'Indicateur opérationnel de délai' as interpretation
        FROM marts.fct_demandes_attribution
        WHERE nb_demandes_finalisees > 0 
          AND delai_traitement_jours > 0;
    """,
    
    'v_kpi_volume_demandes': """
        CREATE OR REPLACE VIEW public.v_kpi_volume_demandes AS
        SELECT 
            'Volume des demandes d''attribution' as indicateur,
            COUNT(DISTINCT demande_id) as total_demandes,
            SUM(nb_demandes_en_cours) as demandes_en_cours,
            SUM(nb_demandes_acceptees) as demandes_acceptees,
            SUM(nb_demandes_rejetees) as demandes_rejetees,
            SUM(nb_demandes_finalisees) as demandes_finalisees,
            SUM(nb_demandes_prioritaires) as demandes_prioritaires,
            SUM(nb_demandes_zone_industrielle) as demandes_zone_industrielle,
            SUM(nb_demandes_hors_zone) as demandes_hors_zone,
            ROUND(
                (SUM(nb_demandes_prioritaires) * 100.0) / 
                NULLIF(COUNT(DISTINCT demande_id), 0), 1
            ) as pourcentage_prioritaires,
            ROUND(
                (SUM(nb_demandes_zone_industrielle) * 100.0) / 
                NULLIF(COUNT(DISTINCT demande_id), 0), 1
            ) as pourcentage_zone_industrielle,
            CURRENT_DATE as date_calcul,
            'Indicateur de volume et répartition' as interpretation
        FROM marts.fct_demandes_attribution;
    """,
    
    'v_kpi_performance_financiere': """
        CREATE OR REPLACE VIEW public.v_kpi_performance_financiere AS
        SELECT 
            'Performance financière et emploi' as indicateur,
            COUNT(DISTINCT demande_id) as nombre_demandes,
            SUM(montant_financement) as montant_total_finance,
            ROUND(AVG(montant_financement)::numeric, 0) as montant_moyen_finance,
            SUM(nombre_emplois) as emplois_total_crees,
            ROUND(AVG(nombre_emplois)::numeric, 1) as emplois_moyen_par_demande,
            ROUND(
                (SUM(montant_financement) / NULLIF(SUM(nombre_emplois), 0))::numeric, 0
            ) as cout_par_emploi,
            SUM(CASE WHEN montant_financement > 0 THEN 1 ELSE 0 END) as demandes_avec_financement,
            SUM(CASE WHEN nombre_emplois > 0 THEN 1 ELSE 0 END) as demandes_avec_emplois,
            ROUND(
                (SUM(CASE WHEN montant_financement > 0 THEN 1 ELSE 0 END) * 100.0) / 
                NULLIF(COUNT(DISTINCT demande_id), 0), 1
            ) as pourcentage_avec_financement,
            CURRENT_DATE as date_calcul,
            'Indicateur économique' as interpretation
        FROM marts.fct_demandes_attribution
        WHERE nb_demandes_acceptees > 0;
    """,
    
    'v_kpi_analyse_temporelle': """
        CREATE OR REPLACE VIEW public.v_kpi_analyse_temporelle AS
        SELECT 
            TO_CHAR(date_creation, 'YYYY-MM') as periode_mois,
            EXTRACT(YEAR FROM date_creation) as annee,
            EXTRACT(MONTH FROM date_creation) as mois,
            COUNT(DISTINCT demande_id) as demandes_creees,
            SUM(nb_demandes_acceptees) as demandes_acceptees,
            SUM(nb_demandes_rejetees) as demandes_rejetees,
            SUM(nb_demandes_prioritaires) as demandes_prioritaires,
            ROUND(AVG(delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            SUM(montant_financement) as montant_finance,
            SUM(nombre_emplois) as emplois_crees,
            ROUND(
                (SUM(nb_demandes_acceptees) * 100.0) / 
                NULLIF(SUM(nb_demandes_finalisees), 0), 1
            ) as taux_acceptation_mensuel,
            ROUND(
                (SUM(nb_demandes_prioritaires) * 100.0) / 
                NULLIF(COUNT(DISTINCT demande_id), 0), 1
            ) as pourcentage_prioritaires_mensuel,
            CURRENT_DATE as date_calcul,
            'Analyse de tendance mensuelle' as interpretation
        FROM marts.fct_demandes_attribution
        WHERE date_creation IS NOT NULL
        GROUP BY 
            TO_CHAR(date_creation, 'YYYY-MM'),
            EXTRACT(YEAR FROM date_creation),
            EXTRACT(MONTH FROM date_creation)
        ORDER BY periode_mois;
    """,
    
    'v_kpi_repartition_geographique': """
        CREATE OR REPLACE VIEW public.v_kpi_repartition_geographique AS
        SELECT 
            dz.nom_zone as zone_industrielle,
            dz.code_zone,
            'Tunisie' as region,
            COUNT(DISTINCT f.demande_id) as total_demandes,
            SUM(f.nb_demandes_acceptees) as demandes_acceptees,
            SUM(f.nb_demandes_en_cours) as demandes_en_cours,
            SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
            ROUND(AVG(f.delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            SUM(f.montant_financement) as montant_total_finance,
            SUM(f.nombre_emplois) as emplois_total_crees,
            ROUND(
                (SUM(f.nb_demandes_acceptees) * 100.0) / 
                NULLIF(SUM(f.nb_demandes_finalisees), 0), 1
            ) as taux_acceptation_zone,
            ROUND(
                (COUNT(DISTINCT f.demande_id) * 100.0) / 
                NULLIF(SUM(COUNT(DISTINCT f.demande_id)) OVER(), 0), 1
            ) as pourcentage_demandes_totales,
            CURRENT_DATE as date_calcul,
            'Analyse géographique par zone' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_zones_industrielles dz ON f.zone_key = dz.zone_key
        GROUP BY dz.nom_zone, dz.code_zone
        ORDER BY total_demandes DESC;
    """,
    
    'v_kpi_tableau_bord_executif': """
        CREATE OR REPLACE VIEW public.v_kpi_tableau_bord_executif AS
        SELECT 
            -- Métriques de volume
            COUNT(DISTINCT demande_id) as total_demandes,
            SUM(nb_demandes_en_cours) as demandes_en_cours,
            SUM(nb_demandes_finalisees) as demandes_finalisees,
            
            -- Taux de performance
            ROUND(
                (SUM(nb_demandes_acceptees) * 100.0) / 
                NULLIF(SUM(nb_demandes_finalisees), 0), 2
            ) as taux_acceptation_pct,
            
            -- Délais
            ROUND(AVG(CASE WHEN nb_demandes_finalisees > 0 THEN delai_traitement_jours END)::numeric, 1) as delai_moyen_jours,
            
            -- Priorités
            SUM(nb_demandes_prioritaires) as demandes_prioritaires,
            ROUND(
                (SUM(nb_demandes_prioritaires) * 100.0) / 
                NULLIF(COUNT(DISTINCT demande_id), 0), 1
            ) as pourcentage_prioritaires,
            
            -- Finance et emploi
            SUM(montant_financement) as montant_total_finance,
            ROUND(AVG(montant_financement)::numeric, 0) as montant_moyen_finance,
            SUM(nombre_emplois) as emplois_total_crees,
            
            -- Répartition par type
            SUM(nb_demandes_zone_industrielle) as demandes_zone_industrielle,
            SUM(nb_demandes_hors_zone) as demandes_hors_zone,
            
            -- Alertes (seuils critiques)
            CASE 
                WHEN ROUND((SUM(nb_demandes_acceptees) * 100.0) / NULLIF(SUM(nb_demandes_finalisees), 0), 2) < 30 
                THEN 'ALERTE: Taux acceptation faible'
                WHEN ROUND(AVG(CASE WHEN nb_demandes_finalisees > 0 THEN delai_traitement_jours END)::numeric, 1) > 15 
                THEN 'ALERTE: Délai traitement élevé'
                ELSE 'NORMAL'
            END as statut_alerte,
            
            -- Métadonnées
            CURRENT_DATE as date_calcul,
            CURRENT_TIMESTAMP as derniere_maj,
            'Tableau de bord exécutif SIGETI' as source
        FROM marts.fct_demandes_attribution;
    """
}

def create_database_connection():
    """Créer une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None

def deploy_views():
    """Déployer toutes les vues KPI"""
    print("🚀 Déploiement des vues KPI SIGETI...")
    print("=" * 50)
    
    conn = create_database_connection()
    if not conn:
        sys.exit(1)
    
    cursor = conn.cursor()
    success_count = 0
    error_count = 0
    
    try:
        for view_name, sql in VIEWS_SQL.items():
            try:
                print(f"📊 Création de la vue: {view_name}")
                cursor.execute(sql)
                success_count += 1
                print(f"   ✅ Vue {view_name} créée avec succès")
            except Exception as e:
                error_count += 1
                print(f"   ❌ Erreur lors de la création de {view_name}: {e}")
        
        print("\n" + "=" * 50)
        print(f"📈 Résumé du déploiement:")
        print(f"   ✅ Vues créées avec succès: {success_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        if error_count == 0:
            print("\n🎉 Toutes les vues KPI ont été déployées avec succès!")
            
            # Lister les vues créées
            print("\n📋 Vues disponibles:")
            for view_name in VIEWS_SQL.keys():
                print(f"   - public.{view_name}")
                
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_views():
    """Tester les vues créées"""
    print("\n🔍 Test des vues créées...")
    
    conn = create_database_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    test_results = {}
    
    try:
        for view_name in VIEWS_SQL.keys():
            try:
                test_sql = f"SELECT COUNT(*) as row_count FROM public.{view_name}"
                cursor.execute(test_sql)
                result = cursor.fetchone()
                test_results[view_name] = {
                    'status': 'SUCCESS',
                    'row_count': result[0] if result else 0
                }
                print(f"   ✅ {view_name}: {result[0] if result else 0} ligne(s)")
            except Exception as e:
                test_results[view_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                print(f"   ❌ {view_name}: Erreur - {e}")
        
        return all(result['status'] == 'SUCCESS' for result in test_results.values())
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print(f"🕐 Début du déploiement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Déployer les vues
    if deploy_views():
        # Tester les vues
        if test_views():
            print(f"\n🎯 Déploiement terminé avec succès: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sys.exit(0)
        else:
            print(f"\n⚠️ Déploiement réussi mais tests échoués: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sys.exit(1)
    else:
        print(f"\n❌ Échec du déploiement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(1)