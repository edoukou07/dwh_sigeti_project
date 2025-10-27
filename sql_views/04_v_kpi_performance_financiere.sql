-- =============================================================================
-- VUE: v_kpi_performance_financiere
-- DESCRIPTION: Indicateurs financiers et d'emploi
-- INDICATEUR: Montants financés et emplois créés
-- =============================================================================

CREATE OR REPLACE VIEW public.v_kpi_performance_financiere AS
SELECT 
    'Performance financière et emploi' as indicateur,
    COUNT(DISTINCT demande_id) as nombre_demandes,
    SUM(montant_financement) as montant_total_finance,
    ROUND(AVG(montant_financement), 0) as montant_moyen_finance,
    SUM(nombre_emplois) as emplois_total_crees,
    ROUND(AVG(nombre_emplois), 1) as emplois_moyen_par_demande,
    ROUND(
        SUM(montant_financement) / NULLIF(SUM(nombre_emplois), 0), 0
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