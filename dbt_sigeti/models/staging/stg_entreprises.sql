-- Modèle de staging pour les entreprises
-- Utilise les données synchronisées depuis SIGETI vers le staging

select
    entreprise_id,
    raison_sociale,
    telephone,
    email,
    registre_commerce,
    compte_contribuable,
    forme_juridique,
    adresse,
    date_constitution,
    domaine_activite_id,
    date_creation,
    date_modification
    
from staging.entreprises