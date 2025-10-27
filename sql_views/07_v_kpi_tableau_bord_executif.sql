-- =============================================================================
-- VUE: v_kpi_tableau_bord_executif
-- DESCRIPTION: Vue consolidée pour tableau de bord exécutif
-- INDICATEUR: Tous les KPI principaux en une seule vue
-- =============================================================================

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
    ROUND(AVG(CASE WHEN nb_demandes_finalisees > 0 THEN delai_traitement_jours END), 1) as delai_moyen_jours,
    
    -- Priorités
    SUM(nb_demandes_prioritaires) as demandes_prioritaires,
    ROUND(
        (SUM(nb_demandes_prioritaires) * 100.0) / 
        NULLIF(COUNT(DISTINCT demande_id), 0), 1
    ) as pourcentage_prioritaires,
    
    -- Finance et emploi
    SUM(montant_financement) as montant_total_finance,
    ROUND(AVG(montant_financement), 0) as montant_moyen_finance,
    SUM(nombre_emplois) as emplois_total_crees,
    
    -- Répartition par type
    SUM(nb_demandes_zone_industrielle) as demandes_zone_industrielle,
    SUM(nb_demandes_hors_zone) as demandes_hors_zone,
    
    -- Alertes (seuils critiques)
    CASE 
        WHEN ROUND((SUM(nb_demandes_acceptees) * 100.0) / NULLIF(SUM(nb_demandes_finalisees), 0), 2) < 30 
        THEN 'ALERTE: Taux acceptation faible'
        WHEN ROUND(AVG(CASE WHEN nb_demandes_finalisees > 0 THEN delai_traitement_jours END), 1) > 15 
        THEN 'ALERTE: Délai traitement élevé'
        ELSE 'NORMAL'
    END as statut_alerte,
    
    -- Métadonnées
    CURRENT_DATE as date_calcul,
    CURRENT_TIMESTAMP as derniere_maj,
    'Tableau de bord exécutif SIGETI' as source
FROM marts.fct_demandes_attribution;