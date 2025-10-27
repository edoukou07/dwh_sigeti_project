-- Table de faits pour les demandes d'attribution
-- Une ligne par demande avec toutes les métriques et clés vers les dimensions

select
    -- Clés étrangères vers les dimensions
    to_char(d.date_creation, 'YYYYMMDD')::int as date_creation_key,
    to_char(d.date_modification, 'YYYYMMDD')::int as date_modification_key,
    
    concat('zone_', d.zone_id) as zone_key,
    concat('lot_', d.lot_id) as lot_key,
    concat('entreprise_', d.entreprise_id) as entreprise_key,
    concat(
        coalesce(d.statut, 'UNKNOWN'), 
        '_', 
        coalesce(d.type_demande, 'UNKNOWN'),
        '_',
        coalesce(cast(d.etape_courante as varchar), '0')
    ) as statut_key,
    
    -- Clé naturelle
    d.demande_id,
    d.reference,
    
    -- Métriques additives
    1 as nombre_demandes,
    coalesce(d.montant_financement, 0) as montant_financement,
    coalesce(d.nombre_emplois_total, 0) as nombre_emplois,
    coalesce(d.delai_traitement_jours, 0) as delai_traitement_jours,
    
    -- Métriques semi-additives (indicateurs 0/1)
    case when d.est_prioritaire then 1 else 0 end as nb_demandes_prioritaires,
    case when d.est_finalisee then 1 else 0 end as nb_demandes_finalisees,
    case when d.est_acceptee then 1 else 0 end as nb_demandes_acceptees,
    case when d.statut = 'REJETE' then 1 else 0 end as nb_demandes_rejetees,
    case when d.statut = 'EN_COURS' then 1 else 0 end as nb_demandes_en_cours,
    case when d.type_demande = 'ZONE_INDUSTRIELLE' then 1 else 0 end as nb_demandes_zone_industrielle,
    case when d.type_demande = 'HORS_ZONE_INDUSTRIELLE' then 1 else 0 end as nb_demandes_hors_zone,
    
    -- Attributs dégénérés (stockés dans la table de faits)
    d.priorite,
    d.etape_courante,
    
    -- Dates importantes
    d.date_creation,
    d.date_modification,
    
    -- Métadonnées
    current_timestamp as dbt_updated_at

from {{ ref('stg_demandes_attribution') }} d