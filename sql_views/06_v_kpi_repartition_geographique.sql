-- =============================================================================
-- VUE: v_kpi_repartition_geographique
-- DESCRIPTION: Répartition géographique des demandes par zone industrielle
-- INDICATEUR: Distribution et performance par zone
-- =============================================================================

CREATE OR REPLACE VIEW public.v_kpi_repartition_geographique AS
SELECT 
    dz.nom_zone as zone_industrielle,
    dz.code_zone,
    dz.region,
    COUNT(DISTINCT f.demande_id) as total_demandes,
    SUM(f.nb_demandes_acceptees) as demandes_acceptees,
    SUM(f.nb_demandes_en_cours) as demandes_en_cours,
    SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen_jours,
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
GROUP BY dz.nom_zone, dz.code_zone, dz.region
ORDER BY total_demandes DESC;