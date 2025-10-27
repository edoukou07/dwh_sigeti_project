-- Dimension des lots

select
    -- Clé surrogate
    concat('lot_', lot_id) as lot_key,
    
    -- Clé naturelle
    lot_id,
    
    -- Attributs du lot
    numero_lot,
    ilot,
    superficie,
    unite_mesure,
    prix,
    statut,
    priorite,
    viabilite,
    description,
    coordonnees,
    zone_industrielle_id,
    
    -- Attributs calculés
    case 
        when statut = 'disponible' then 'Disponible'
        when statut = 'occupé' then 'Occupé'
        else 'Autre'
    end as statut_libelle,
    
    case 
        when priorite = 'normale' then 'Normal'
        when priorite = 'haute' then 'Haute Priorité'
        else 'Autre'
    end as priorite_libelle,
    
    case 
        when viabilite = true then 'Viabilisé'
        else 'Non Viabilisé'
    end as viabilite_libelle,
    
    case 
        when unite_mesure = 'ha' then superficie
        when unite_mesure = 'm2' then superficie / 10000
        else superficie
    end as superficie_hectares,
    
    -- Métadonnées
    date_creation,
    date_modification,
    current_timestamp as dbt_updated_at

from {{ ref('stg_lots') }}