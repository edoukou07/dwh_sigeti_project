-- Dimension des statuts de demandes

select
    -- Clé surrogate
    concat(
        coalesce(statut, 'UNKNOWN'), 
        '_', 
        coalesce(type_demande, 'UNKNOWN'),
        '_',
        coalesce(cast(etape_courante as varchar), '0')
    ) as statut_key,
    
    -- Attributs du statut
    statut,
    type_demande,
    etape_courante,
    
    -- Libellés lisibles
    case 
        when statut = 'EN_COURS' then 'En Cours'
        when statut = 'VALIDE' then 'Validée'
        when statut = 'REJETE' then 'Rejetée'
        when statut = 'DOCUMENTS_REJETES' then 'Documents Rejetés'
        else 'Inconnu'
    end as statut_libelle,
    
    case 
        when type_demande = 'ZONE_INDUSTRIELLE' then 'Zone Industrielle'
        when type_demande = 'HORS_ZONE_INDUSTRIELLE' then 'Hors Zone Industrielle'
        else 'Inconnu'
    end as type_demande_libelle,
    
    -- Indicateurs booléens
    case when statut = 'VALIDE' then 1 else 0 end as est_validee,
    case when statut = 'REJETE' then 1 else 0 end as est_rejetee,
    case when statut = 'EN_COURS' then 1 else 0 end as est_en_cours,
    case when statut in ('VALIDE', 'REJETE') then 1 else 0 end as est_finalisee,
    case when type_demande = 'ZONE_INDUSTRIELLE' then 1 else 0 end as est_zone_industrielle,
    
    -- Métadonnées
    current_timestamp as dbt_updated_at

from (
    select distinct 
        statut,
        type_demande,
        etape_courante
    from {{ ref('stg_demandes_attribution') }}
    where statut is not null 
      and type_demande is not null
) as statuts_uniques