-- ============================================================================
-- INDICATEURS DE GESTION DES DEMANDES D'ATTRIBUTION
-- Requêtes SQL pour exploiter le modèle en étoile
-- ============================================================================

-- A.1 NOMBRE DE DEMANDES D'ATTRIBUTION PAR STATUT
-- ============================================================================
SELECT 
    ds.statut_libelle,
    ds.statut,
    COUNT(*) as nombre_demandes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pourcentage
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.statut_libelle, ds.statut
ORDER BY nombre_demandes DESC;

-- A.2 NOMBRE DE DEMANDES PAR TYPE (ZONE_INDUSTRIELLE vs HORS_ZONE_INDUSTRIELLE)  
-- ============================================================================
SELECT 
    ds.type_demande_libelle,
    ds.type_demande,
    COUNT(*) as nombre_demandes,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pourcentage
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.type_demande_libelle, ds.type_demande
ORDER BY nombre_demandes DESC;

-- A.3 NOMBRE DE DEMANDES PAR ZONE INDUSTRIELLE, LOT ET ENTREPRISE
-- ============================================================================
SELECT 
    dz.nom_zone,
    dl.numero_lot,
    de.raison_sociale,
    COUNT(*) as nombre_demandes,
    SUM(f.montant_financement) as financement_total,
    SUM(f.nombre_emplois) as emplois_prevus
FROM marts.fct_demandes_attribution f
LEFT JOIN marts.dim_zones_industrielles dz ON f.zone_key = dz.zone_key
LEFT JOIN marts.dim_lots dl ON f.lot_key = dl.lot_key  
LEFT JOIN marts.dim_entreprises de ON f.entreprise_key = de.entreprise_key
GROUP BY dz.nom_zone, dl.numero_lot, de.raison_sociale
ORDER BY nombre_demandes DESC, financement_total DESC;

-- A.4 NOMBRE DE DEMANDES PRIORITAIRES VS NORMALES
-- ============================================================================
SELECT 
    CASE WHEN f.nb_demandes_prioritaires = 1 THEN 'Prioritaire' ELSE 'Normale' END as type_priorite,
    COUNT(*) as nombre_demandes,
    ROUND(AVG(f.montant_financement), 2) as financement_moyen,
    ROUND(AVG(f.nombre_emplois), 0) as emplois_moyens,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen_jours
FROM marts.fct_demandes_attribution f
GROUP BY CASE WHEN f.nb_demandes_prioritaires = 1 THEN 'Prioritaire' ELSE 'Normale' END
ORDER BY nombre_demandes DESC;

-- A.5 DÉLAI MOYEN DE TRAITEMENT D'UNE DEMANDE (création → validation/rejet)
-- ============================================================================
SELECT 
    ds.statut_libelle,
    ds.type_demande_libelle,
    COUNT(*) as nombre_demandes,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen_jours,
    ROUND(MIN(f.delai_traitement_jours), 1) as delai_min_jours,
    ROUND(MAX(f.delai_traitement_jours), 1) as delai_max_jours,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.delai_traitement_jours), 1) as delai_median_jours
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
WHERE f.delai_traitement_jours > 0
GROUP BY ds.statut_libelle, ds.type_demande_libelle
ORDER BY delai_moyen_jours DESC;

-- A.6 TAUX D'ACCEPTATION/APPROBATION DES DEMANDES
-- ============================================================================
SELECT 
    ds.type_demande_libelle,
    COUNT(*) as total_demandes,
    SUM(f.nb_demandes_acceptees) as demandes_acceptees,
    SUM(f.nb_demandes_rejetees) as demandes_rejetees,
    SUM(f.nb_demandes_finalisees) as demandes_finalisees,
    SUM(f.nb_demandes_en_cours) as demandes_en_cours,
    
    -- Taux d'acceptation par rapport aux demandes finalisées
    CASE WHEN SUM(f.nb_demandes_finalisees) > 0 
         THEN ROUND(SUM(f.nb_demandes_acceptees) * 100.0 / SUM(f.nb_demandes_finalisees), 2)
         ELSE 0 END as taux_acceptation_pct,
         
    -- Taux de finalisation par rapport au total
    ROUND(SUM(f.nb_demandes_finalisees) * 100.0 / COUNT(*), 2) as taux_finalisation_pct
    
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.type_demande_libelle
ORDER BY taux_acceptation_pct DESC;

-- A.7 ÉVOLUTION DES DEMANDES PRIORITAIRES PAR PÉRIODE
-- ============================================================================
SELECT 
    dd.annee,
    dd.mois_nom_fr,
    dd.annee_mois,
    SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
    COUNT(*) - SUM(f.nb_demandes_prioritaires) as demandes_normales,
    COUNT(*) as total_demandes,
    ROUND(SUM(f.nb_demandes_prioritaires) * 100.0 / COUNT(*), 2) as pct_prioritaires
FROM marts.fct_demandes_attribution f
JOIN marts.dim_date dd ON f.date_creation_key = dd.date_key
GROUP BY dd.annee, dd.mois, dd.mois_nom_fr, dd.annee_mois
ORDER BY dd.annee, dd.mois;

-- ============================================================================
-- REQUÊTES D'ANALYSE AVANCÉE
-- ============================================================================

-- ANALYSE PAR ZONE INDUSTRIELLE - TOP 10
-- ============================================================================
SELECT 
    dz.nom_zone,
    dz.code_zone,
    dz.statut_libelle,
    COUNT(*) as nombre_demandes,
    SUM(f.nb_demandes_acceptees) as demandes_acceptees,
    SUM(f.montant_financement) as financement_total,
    SUM(f.nombre_emplois) as emplois_prevus,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen
FROM marts.fct_demandes_attribution f
JOIN marts.dim_zones_industrielles dz ON f.zone_key = dz.zone_key
WHERE dz.zone_key IS NOT NULL
GROUP BY dz.nom_zone, dz.code_zone, dz.statut_libelle
ORDER BY nombre_demandes DESC
LIMIT 10;

-- ÉVOLUTION MENSUELLE COMPLÈTE
-- ============================================================================
SELECT 
    dd.annee_mois,
    COUNT(*) as total_demandes,
    SUM(f.nb_demandes_zone_industrielle) as demandes_zone_industrielle,
    SUM(f.nb_demandes_hors_zone) as demandes_hors_zone,
    SUM(f.nb_demandes_prioritaires) as demandes_prioritaires,
    SUM(f.nb_demandes_acceptees) as demandes_acceptees,
    SUM(f.nb_demandes_rejetees) as demandes_rejetees,
    SUM(f.nb_demandes_en_cours) as demandes_en_cours,
    ROUND(AVG(f.delai_traitement_jours), 1) as delai_moyen,
    SUM(f.montant_financement) as financement_total,
    SUM(f.nombre_emplois) as emplois_total
FROM marts.fct_demandes_attribution f
JOIN marts.dim_date dd ON f.date_creation_key = dd.date_key
GROUP BY dd.annee_mois
ORDER BY dd.annee_mois;