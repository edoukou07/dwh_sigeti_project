-- =============================================================================
-- VUE: v_kpi_taux_acceptation
-- DESCRIPTION: Calcule le taux d'acceptation des demandes d'attribution
-- INDICATEUR: Pourcentage de demandes acceptées sur le total des demandes finalisées
-- =============================================================================

CREATE OR REPLACE VIEW public.v_kpi_taux_acceptation AS
SELECT 
    'Taux d''acceptation des demandes' as indicateur,
    ROUND(
        (SUM(nb_demandes_acceptees) * 100.0) / 
        NULLIF(SUM(nb_demandes_finalisees), 0), 2
    ) as valeur_pourcentage,
    SUM(nb_demandes_acceptees) as demandes_acceptees,
    SUM(nb_demandes_finalisees) as demandes_finalisees,
    COUNT(DISTINCT demande_id) as total_demandes,
    CURRENT_DATE as date_calcul,
    'Indicateur stratégique de performance' as interpretation
FROM marts.fct_demandes_attribution
WHERE nb_demandes_finalisees > 0;

COMMENT ON VIEW public.v_kpi_taux_acceptation IS 
'Vue KPI: Taux d''acceptation des demandes d''attribution. Mesure l''efficacité du processus d''approbation.';