-- Dimension des entreprises
-- SCD Type 1 : mise à jour sur place des changements

-- Configuration: table matérialisée
select
    -- Clé surrogate
    'entreprise_' || cast(entreprise_id as varchar) as entreprise_key,
    
    -- Clé naturelle
    entreprise_id,
    
    -- Attributs de l'entreprise
    raison_sociale,
    telephone,
    email,
    registre_commerce,
    compte_contribuable,
    forme_juridique,
    adresse,
    date_constitution,
    domaine_activite_id,
    
    -- Attributs calculés
    case 
        when forme_juridique ilike '%sarl%' then 'SARL'
        when forme_juridique ilike '%sa%' then 'SA'
        when forme_juridique ilike '%sci%' then 'SCI'
        when forme_juridique ilike '%eurl%' then 'EURL'
        else 'AUTRE'
    end as type_forme_juridique,
    
    -- Métadonnées
    date_creation,
    date_modification,
    current_timestamp as dbt_updated_at

from {{ ref('stg_entreprises') }}