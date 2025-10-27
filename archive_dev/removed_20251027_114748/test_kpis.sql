-- Test des KPIs - SIGETI DWH Demandes d'Attribution
-- Requêtes de validation du modèle en étoile

-- 1. Vérification des comptes de base
SELECT 'Nombre total de demandes' as indicateur, COUNT(*) as valeur
FROM marts_marts.fct_demandes_attribution;

-- 2. Répartition par statut
SELECT 
    ds.statut_libelle,
    COUNT(*) as nombre_demandes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pourcentage
FROM marts_marts.fct_demandes_attribution f
JOIN marts_marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.statut_libelle
ORDER BY nombre_demandes DESC;

-- 3. Répartition par type de demande
SELECT 
    ds.type_demande_libelle,
    COUNT(*) as nombre_demandes,
    SUM(f.montant_financement) as financement_total,
    AVG(f.nombre_emplois) as emplois_moyens
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.type_demande_libelle;

-- 4. Analyse des délais de traitement
SELECT 
    ds.statut_libelle,
    COUNT(*) as nb_demandes,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen_jours,
    MIN(f.delai_traitement_jours) as delai_min,
    MAX(f.delai_traitement_jours) as delai_max
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
WHERE f.delai_traitement_jours > 0
GROUP BY ds.statut_libelle;

-- 5. Demandes prioritaires vs normales
SELECT 
    CASE WHEN f.nb_demandes_prioritaires = 1 THEN 'Prioritaire' ELSE 'Normale' END as priorite,
    COUNT(*) as nombre_demandes,
    ROUND(AVG(f.montant_financement), 0) as financement_moyen,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen
FROM marts.fct_demandes_attribution f
GROUP BY CASE WHEN f.nb_demandes_prioritaires = 1 THEN 'Prioritaire' ELSE 'Normale' END;