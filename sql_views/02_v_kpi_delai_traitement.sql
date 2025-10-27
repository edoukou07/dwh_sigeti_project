-- =============================================================================
-- VUE: v_kpi_delai_traitement
-- DESCRIPTION: Calcule les métriques de délai de traitement des demandes
-- INDICATEUR: Délai moyen, médian et distribution des temps de traitement
-- =============================================================================

CREATE OR REPLACE VIEW public.v_kpi_delai_traitement AS
SELECT 
    'Délai de traitement des demandes' as indicateur,
    ROUND(AVG(delai_traitement_jours), 1) as delai_moyen_jours,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delai_traitement_jours), 1) as delai_median_jours,
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