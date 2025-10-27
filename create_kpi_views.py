"""
Script Python pour créer et déployer les 7 vues KPI SIGETI spécifiques
Adapté aux besoins métier précis des demandes d'attribution
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

# Définition des 7 vues KPI spécifiques demandées
VIEWS_SQL = {
    # KPI 1: Nombre de demandes d'attribution par statut (EN_COURS, VALIDÉE, REJETÉE)
    'v_kpi_demandes_par_statut': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_statut AS
        SELECT 
            'Demandes par statut' as indicateur,
            CASE 
                WHEN f.nb_demandes_en_cours > 0 THEN 'EN_COURS'
                WHEN f.nb_demandes_acceptees > 0 THEN 'VALIDÉE'
                WHEN f.nb_demandes_rejetees > 0 THEN 'REJETÉE'
                ELSE 'AUTRE'
            END as statut,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT f.demande_id) * 100.0 / SUM(COUNT(DISTINCT f.demande_id)) OVER(), 2) as pourcentage,
            SUM(f.montant_financement) as montant_total,
            SUM(f.nombre_emplois) as emplois_total,
            CURRENT_DATE as date_calcul,
            'Répartition des demandes selon leur statut : EN_COURS, VALIDÉE, REJETÉE' as interpretation
        FROM marts.fct_demandes_attribution f
        GROUP BY 
            CASE 
                WHEN f.nb_demandes_en_cours > 0 THEN 'EN_COURS'
                WHEN f.nb_demandes_acceptees > 0 THEN 'VALIDÉE'
                WHEN f.nb_demandes_rejetees > 0 THEN 'REJETÉE'
                ELSE 'AUTRE'
            END
        ORDER BY nombre_demandes DESC;
    """,

    # KPI 2: Nombre de demandes par type (ZONE_INDUSTRIELLE, HORS_ZONE_INDUSTRIELLE)
    'v_kpi_demandes_par_type': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_type AS
        SELECT 
            'Demandes par type de zone' as indicateur,
            CASE 
                WHEN f.nb_demandes_zone_industrielle > 0 THEN 'ZONE_INDUSTRIELLE'
                ELSE 'HORS_ZONE_INDUSTRIELLE'
            END as type_zone,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT f.demande_id) * 100.0 / SUM(COUNT(DISTINCT f.demande_id)) OVER(), 2) as pourcentage,
            SUM(f.montant_financement) as montant_total,
            SUM(f.nombre_emplois) as emplois_total,
            AVG(f.delai_traitement_jours) as delai_moyen_jours,
            CURRENT_DATE as date_calcul,
            'Répartition entre demandes en zone industrielle et hors zone' as interpretation
        FROM marts.fct_demandes_attribution f
        GROUP BY 
            CASE 
                WHEN f.nb_demandes_zone_industrielle > 0 THEN 'ZONE_INDUSTRIELLE'
                ELSE 'HORS_ZONE_INDUSTRIELLE'
            END
        ORDER BY nombre_demandes DESC;
    """,

    # KPI 3: Nombre de demandes par zone industrielle, lot et entreprise
    'v_kpi_demandes_par_entite': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_par_entite AS
        SELECT 
            'Demandes par entité géographique et organisationnelle' as indicateur,
            z.nom_zone as zone_industrielle,
            l.numero_lot as lot,
            e.raison_sociale as entreprise,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            SUM(f.montant_financement) as montant_total_finance,
            SUM(f.nombre_emplois) as emplois_crees,
            ROUND(AVG(f.delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            SUM(f.nb_demandes_acceptees) as demandes_validees,
            SUM(f.nb_demandes_rejetees) as demandes_rejetees,
            SUM(f.nb_demandes_en_cours) as demandes_en_cours,
            CURRENT_DATE as date_calcul,
            'Analyse détaillée par zone industrielle, lot et entreprise' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_zones_industrielles z ON f.zone_key = z.zone_key
        JOIN marts.dim_lots l ON f.lot_key = l.lot_key
        JOIN marts.dim_entreprises e ON f.entreprise_key = e.entreprise_key
        GROUP BY z.nom_zone, l.numero_lot, e.raison_sociale
        ORDER BY nombre_demandes DESC, montant_total_finance DESC;
    """,

    # KPI 4: Nombre de demandes prioritaires vs normales
    'v_kpi_demandes_prioritaires': """
        CREATE OR REPLACE VIEW public.v_kpi_demandes_prioritaires AS
        SELECT 
            'Demandes prioritaires vs normales' as indicateur,
            CASE 
                WHEN f.nb_demandes_prioritaires > 0 THEN 'PRIORITAIRE'
                ELSE 'NORMALE'
            END as niveau_priorite,
            COUNT(DISTINCT f.demande_id) as nombre_demandes,
            ROUND(COUNT(DISTINCT f.demande_id) * 100.0 / SUM(COUNT(DISTINCT f.demande_id)) OVER(), 2) as pourcentage,
            SUM(f.montant_financement) as montant_total,
            SUM(f.nombre_emplois) as emplois_total,
            ROUND(AVG(f.delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            SUM(f.nb_demandes_acceptees) as demandes_validees,
            CURRENT_DATE as date_calcul,
            'Comparaison entre demandes prioritaires et normales' as interpretation
        FROM marts.fct_demandes_attribution f
        GROUP BY 
            CASE 
                WHEN f.nb_demandes_prioritaires > 0 THEN 'PRIORITAIRE'
                ELSE 'NORMALE'
            END
        ORDER BY niveau_priorite DESC;
    """,

    # KPI 5: Délai moyen de traitement d'une demande (création → validation/rejet)
    'v_kpi_delai_traitement': """
        CREATE OR REPLACE VIEW public.v_kpi_delai_traitement AS
        SELECT 
            'Délai de traitement des demandes' as indicateur,
            ROUND(AVG(f.delai_traitement_jours)::numeric, 1) as delai_moyen_jours,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.delai_traitement_jours)::numeric, 1) as delai_median_jours,
            MIN(f.delai_traitement_jours) as delai_min_jours,
            MAX(f.delai_traitement_jours) as delai_max_jours,
            COUNT(DISTINCT CASE WHEN f.delai_traitement_jours <= 7 THEN f.demande_id END) as demandes_sous_7j,
            COUNT(DISTINCT CASE WHEN f.delai_traitement_jours BETWEEN 8 AND 15 THEN f.demande_id END) as demandes_8_15j,
            COUNT(DISTINCT CASE WHEN f.delai_traitement_jours > 15 THEN f.demande_id END) as demandes_plus_15j,
            COUNT(DISTINCT CASE WHEN f.nb_demandes_finalisees > 0 THEN f.demande_id END) as total_demandes_finalisees,
            CURRENT_DATE as date_calcul,
            'Analyse des délais depuis création jusqu''à validation/rejet' as interpretation
        FROM marts.fct_demandes_attribution f
        WHERE f.delai_traitement_jours IS NOT NULL AND f.delai_traitement_jours > 0;
    """,

    # KPI 6: Taux d'acceptation/approbation des demandes
    'v_kpi_taux_acceptation': """
        CREATE OR REPLACE VIEW public.v_kpi_taux_acceptation AS
        SELECT 
            'Taux d''acceptation des demandes' as indicateur,
            ROUND(
                (SUM(f.nb_demandes_acceptees) * 100.0) / 
                NULLIF(SUM(f.nb_demandes_finalisees), 0), 2
            ) as taux_acceptation_pourcentage,
            SUM(f.nb_demandes_acceptees) as demandes_validees,
            SUM(f.nb_demandes_rejetees) as demandes_rejetees,
            SUM(f.nb_demandes_en_cours) as demandes_en_cours,
            SUM(f.nb_demandes_finalisees) as demandes_finalisees,
            COUNT(DISTINCT f.demande_id) as total_demandes,
            ROUND(
                (SUM(f.nb_demandes_rejetees) * 100.0) / 
                NULLIF(SUM(f.nb_demandes_finalisees), 0), 2
            ) as taux_rejet_pourcentage,
            CURRENT_DATE as date_calcul,
            'Ratio des demandes acceptées (validées) par rapport aux demandes traitées' as interpretation
        FROM marts.fct_demandes_attribution f;
    """,

    # KPI 7: Évolution des demandes prioritaires par période
    'v_kpi_evolution_prioritaires': """
        CREATE OR REPLACE VIEW public.v_kpi_evolution_prioritaires AS
        SELECT 
            'Évolution demandes prioritaires par période' as indicateur,
            d.annee,
            d.mois,
            d.mois_nom_fr,
            d.trimestre,
            COUNT(DISTINCT f.demande_id) as total_demandes,
            SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
            COUNT(DISTINCT f.demande_id) - SUM(f.nb_demandes_prioritaires) as demandes_normales,
            ROUND(
                (SUM(f.nb_demandes_prioritaires) * 100.0) / 
                NULLIF(COUNT(DISTINCT f.demande_id), 0), 2
            ) as pourcentage_prioritaires,
            SUM(f.montant_financement) as montant_total_periode,
            SUM(f.nombre_emplois) as emplois_total_periode,
            ROUND(AVG(f.delai_traitement_jours)::numeric, 1) as delai_moyen_periode,
            CURRENT_DATE as date_calcul,
            'Évolution temporelle de la proportion de demandes prioritaires' as interpretation
        FROM marts.fct_demandes_attribution f
        JOIN marts.dim_date d ON f.date_creation_key = d.date_key
        GROUP BY d.annee, d.mois, d.mois_nom_fr, d.trimestre
        ORDER BY d.annee, d.mois;
    """
}

def create_connection():
    """Créer une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        sys.exit(1)

def create_view(cursor, view_name, view_sql):
    """Créer une vue KPI"""
    try:
        print(f"Création de la vue {view_name}...")
        cursor.execute(view_sql)
        print(f"✓ Vue {view_name} créée avec succès")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de la création de {view_name}: {e}")
        return False

def validate_view(cursor, view_name):
    """Valider qu'une vue fonctionne correctement"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM public.{view_name}")
        count = cursor.fetchone()[0]
        print(f"  → Validation: {view_name} contient {count} lignes")
        return True
    except Exception as e:
        print(f"  → Erreur validation {view_name}: {e}")
        return False

def main():
    """Fonction principale pour créer toutes les vues KPI"""
    
    print("=== CRÉATION DES 7 VUES KPI SIGETI ===")
    print(f"Connexion à la base: {DB_CONFIG['database']}")
    
    # Connexion
    conn = create_connection()
    cursor = conn.cursor()
    
    # Compteurs
    created_views = 0
    total_views = len(VIEWS_SQL)
    
    # Création des vues
    print(f"\nCréation de {total_views} vues KPI...")
    
    for view_name, view_sql in VIEWS_SQL.items():
        if create_view(cursor, view_name, view_sql):
            if validate_view(cursor, view_name):
                created_views += 1
    
    # Résumé final
    print(f"\n=== RÉSUMÉ ===")
    print(f"Vues créées avec succès: {created_views}/{total_views}")
    
    if created_views == total_views:
        print("🎉 Toutes les vues KPI ont été créées et validées!")
        print("\nVues disponibles pour le reporting:")
        for i, view_name in enumerate(VIEWS_SQL.keys(), 1):
            kpi_descriptions = [
                "Nombre de demandes par statut (EN_COURS, VALIDÉE, REJETÉE)",
                "Nombre de demandes par type (ZONE_INDUSTRIELLE, HORS_ZONE_INDUSTRIELLE)", 
                "Nombre de demandes par zone industrielle, lot et entreprise",
                "Nombre de demandes prioritaires vs normales",
                "Délai moyen de traitement d'une demande (création → validation/rejet)",
                "Taux d'acceptation/approbation des demandes",
                "Évolution des demandes prioritaires par période"
            ]
            print(f"  {i}. {view_name} → {kpi_descriptions[i-1]}")
    else:
        print(f"⚠️ Problèmes détectés. Vérifiez les erreurs ci-dessus.")
    
    # Fermeture
    cursor.close()
    conn.close()
    
    print(f"\nScript terminé le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()