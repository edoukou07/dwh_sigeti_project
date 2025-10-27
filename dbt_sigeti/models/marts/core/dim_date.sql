-- Dimension temporelle standard
-- Génère une table de dates pour les analyses temporelles

with date_spine as (
    select 
        generate_series(
            '2020-01-01'::date,
            '2030-12-31'::date,
            interval '1 day'
        )::date as date_day
)

select
    -- Clé surrogate (YYYYMMDD)
    to_char(date_day, 'YYYYMMDD')::int as date_key,
    
    -- Date complète
    date_day as date_complete,
    
    -- Composants de la date
    extract(year from date_day) as annee,
    extract(month from date_day) as mois,
    extract(day from date_day) as jour,
    extract(quarter from date_day) as trimestre,
    extract(dow from date_day) as jour_semaine_num, -- 0=dimanche, 6=samedi
    extract(doy from date_day) as jour_annee,
    extract(week from date_day) as semaine_annee,
    
    -- Libellés
    to_char(date_day, 'Month') as mois_nom,
    to_char(date_day, 'Mon') as mois_nom_court,
    to_char(date_day, 'Day') as jour_semaine_nom,
    to_char(date_day, 'Dy') as jour_semaine_nom_court,
    
    case extract(dow from date_day)
        when 0 then 'Dimanche'
        when 1 then 'Lundi'
        when 2 then 'Mardi'
        when 3 then 'Mercredi'
        when 4 then 'Jeudi'
        when 5 then 'Vendredi'
        when 6 then 'Samedi'
    end as jour_semaine_fr,
    
    case extract(month from date_day)
        when 1 then 'Janvier'
        when 2 then 'Février'
        when 3 then 'Mars'
        when 4 then 'Avril'
        when 5 then 'Mai'
        when 6 then 'Juin'
        when 7 then 'Juillet'
        when 8 then 'Août'
        when 9 then 'Septembre'
        when 10 then 'Octobre'
        when 11 then 'Novembre'
        when 12 then 'Décembre'
    end as mois_nom_fr,
    
    -- Périodes
    concat('Q', extract(quarter from date_day), '-', extract(year from date_day)) as trimestre_libelle,
    to_char(date_day, 'YYYY-MM') as annee_mois,
    
    -- Indicateurs
    case when extract(dow from date_day) in (0, 6) then true else false end as est_weekend,
    case when extract(dow from date_day) in (1, 2, 3, 4, 5) then true else false end as est_jour_ouvrable,
    
    -- Décalages temporels
    date_day - interval '1 day' as date_precedente,
    date_day + interval '1 day' as date_suivante,
    
    -- Métadonnées
    current_timestamp as dbt_updated_at

from date_spine
order by date_day