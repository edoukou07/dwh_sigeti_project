-- =============================================================================
-- VUE: v_kpi_analyse_temporelle
-- DESCRIPTION: Analyse des tendances temporelles des demandes
-- INDICATEUR: Évolution mensuelle des demandes et performance
-- =============================================================================

CREATE OR REPLACE VIEW public.v_kpi_analyse_temporelle AS
SELECT 
    TO_CHAR(date_creation, 'YYYY-MM') as periode_mois,
    EXTRACT(YEAR FROM date_creation) as annee,
    EXTRACT(MONTH FROM date_creation) as mois,
    COUNT(DISTINCT demande_id) as demandes_creees,
    SUM(nb_demandes_acceptees) as demandes_acceptees,
    SUM(nb_demandes_rejetees) as demandes_rejetees,
    SUM(nb_demandes_prioritaires) as demandes_prioritaires,
    ROUND(AVG(delai_traitement_jours), 1) as delai_moyen_jours,
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