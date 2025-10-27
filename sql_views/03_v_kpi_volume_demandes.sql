-- =============================================================================
-- VUE: v_kpi_volume_demandes
-- DESCRIPTION: Suivi du volume et de la répartition des demandes
-- INDICATEUR: Nombre total de demandes par statut et type
-- =============================================================================

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