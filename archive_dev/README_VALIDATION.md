# Guide de Validation et Tests du Modèle en Étoile

## 🧪 Tests de Validation à Exécuter

### 1. Vérification des Comptes de Base
```sql
-- Vérifier que le nombre de demandes correspond
SELECT 
    'Source' as table_type, 
    COUNT(*) as nb_demandes 
FROM public.demandes_attribution
UNION ALL
SELECT 
    'DWH' as table_type, 
    COUNT(*) as nb_demandes 
FROM marts.fct_demandes_attribution;
```

### 2. Validation des Statuts
```sql
-- Vérifier la répartition des statuts
SELECT 
    statut, 
    COUNT(*) as count_source
FROM public.demandes_attribution 
GROUP BY statut
ORDER BY statut;

-- Vs DWH
SELECT 
    ds.statut,
    COUNT(*) as count_dwh
FROM marts.fct_demandes_attribution f
JOIN marts.dim_statuts_demandes ds ON f.statut_key = ds.statut_key
GROUP BY ds.statut
ORDER BY ds.statut;
```

### 3. Test des Jointures
```sql
-- Vérifier qu'il n'y a pas de pertes de données dans les jointures
SELECT 
    'Demandes sans zone' as probleme,
    COUNT(*) as nb_problemes
FROM marts.fct_demandes_attribution f
WHERE f.zone_key IS NULL AND f.zone_key != 'zone_'
UNION ALL
SELECT 
    'Demandes sans entreprise' as probleme,
    COUNT(*) as nb_problemes  
FROM marts.fct_demandes_attribution f
WHERE f.entreprise_key IS NULL AND f.entreprise_key != 'entreprise_';
```

## 📊 Tableaux de Bord Recommandés

### Dashboard Exécutif
- **KPI Principal :** Taux d'acceptation global
- **Tendances :** Évolution mensuelle des demandes
- **Alertes :** Délais de traitement > 30 jours

### Dashboard Opérationnel  
- **Détail par Zone :** Performance de chaque zone industrielle
- **Pipeline des Demandes :** Statut actuel et goulots d'étranglement
- **Analyse des Rejets :** Causes principales de refus

## 🚀 Commandes de Déploiement

### Installation initiale
```bash
# 1. Initialiser dbt
cd /opt/dbt/sigeti_dwh
dbt init

# 2. Installer les dépendances
dbt deps

# 3. Test de connexion
dbt debug

# 4. Première exécution complète
dbt run --full-refresh

# 5. Exécution des tests
dbt test

# 6. Génération de la documentation
dbt docs generate
dbt docs serve
```

### Mise à jour quotidienne
```bash
# Mise à jour incrémentale (via Airflow ou manuel)
dbt run
dbt test
```

## 📈 Métriques de Performance Attendues

### Volumétrie Estimée
- **dim_date :** ~4 000 lignes (2020-2030)
- **dim_entreprises :** Variable selon votre base
- **dim_zones_industrielles :** Variable selon votre base  
- **dim_lots :** Variable selon votre base
- **fct_demandes_attribution :** 1 ligne = 1 demande

### Temps d'Exécution
- **Staging :** < 30 secondes
- **Dimensions :** < 2 minutes
- **Table de faits :** < 1 minute
- **Total pipeline :** < 5 minutes