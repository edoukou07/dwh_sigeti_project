-- Dimension des zones industrielles

select
    -- Clé surrogate
    concat('zone_', zone_id) as zone_key,
    
    -- Clé naturelle
    zone_id,
    
    -- Attributs de la zone
    code_zone,
    libelle as nom_zone,
    description,
    superficie,
    unite_mesure,
    lots_disponibles,
    adresse,
    statut,
    
    -- Attributs calculés
    case 
        when statut = 'actif' then 'Active'
        when statut = 'inactif' then 'Inactive'
        when statut = 'en_construction' then 'En Construction'
        else 'Autre'
    end as statut_libelle,
    
    case 
        when unite_mesure = 'ha' then superficie
        when unite_mesure = 'm2' then superficie / 10000
        else superficie
    end as superficie_hectares,
    
    -- Métadonnées
    date_creation,
    date_modification,
    current_timestamp as dbt_updated_at

from {{ ref('stg_zones_industrielles') }}