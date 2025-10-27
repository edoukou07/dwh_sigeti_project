-- Modèle de staging pour les demandes d'attribution
-- Utilise les données synchronisées depuis SIGETI vers le staging

select
    demande_id,
    reference,
    statut,
    etape_courante,
    type_demande,
    operateur_id,
    entreprise_id,
    lot_id,
    zone_id,
    priorite,
    montant_financement,
    nombre_emplois_total,
    est_prioritaire,
    date_creation,
    date_modification,
    delai_traitement_jours,
    est_finalisee,
    est_acceptee

from staging.demandes_attribution