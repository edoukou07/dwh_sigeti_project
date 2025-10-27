-- Modèle de staging pour les zones industrielles
-- Utilise les données synchronisées depuis SIGETI vers le staging

select
    zone_id,
    code_zone,
    libelle,
    description,
    superficie,
    unite_mesure,
    lots_disponibles,
    adresse,
    statut,
    date_creation,
    date_modification
    
from staging.zones_industrielles