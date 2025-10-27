-- Modèle de staging pour les lots
-- Utilise les données synchronisées depuis SIGETI vers le staging

select
    lot_id,
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
    entreprise_id,
    operateur_id,
    date_acquisition,
    date_reservation,
    delai_option,
    date_creation,
    date_modification
    
from staging.lots