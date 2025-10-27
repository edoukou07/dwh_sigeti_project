# Vues KPI SIGETI - Documentation

## 📊 Vue d'ensemble

Ce répertoire contient les vues SQL pour les indicateurs de performance (KPI) du système SIGETI. Ces vues permettent d'analyser les demandes d'attribution et de générer des rapports de performance.

## 🎯 Indicateurs disponibles

### 1. **v_kpi_taux_acceptation**
- **Objectif**: Mesurer l'efficacité du processus d'approbation
- **Métrique principale**: Pourcentage de demandes acceptées
- **Utilisation**: Tableau de bord exécutif, rapports de performance

### 2. **v_kpi_delai_traitement** 
- **Objectif**: Analyser les temps de traitement des demandes
- **Métriques**: Délai moyen, médian, distribution temporelle
- **Utilisation**: Optimisation des processus, SLA monitoring

### 3. **v_kpi_volume_demandes**
- **Objectif**: Suivre le volume et la répartition des demandes
- **Métriques**: Nombre total, répartition par statut et type
- **Utilisation**: Planification des ressources, analyse des tendances

### 4. **v_kpi_performance_financiere**
- **Objectif**: Mesurer l'impact économique des attributions
- **Métriques**: Montants financés, emplois créés, coût par emploi
- **Utilisation**: Rapports financiers, ROI analysis

### 5. **v_kpi_analyse_temporelle**
- **Objectif**: Analyser l'évolution des demandes dans le temps
- **Métriques**: Tendances mensuelles, saisonnalité
- **Utilisation**: Prévisions, planification stratégique

### 6. **v_kpi_repartition_geographique**
- **Objectif**: Analyser la distribution géographique des demandes
- **Métriques**: Performance par zone industrielle et région
- **Utilisation**: Aménagement du territoire, allocation des ressources

### 7. **v_kpi_tableau_bord_executif**
- **Objectif**: Vue consolidée pour la direction
- **Métriques**: Tous les KPI principaux en une seule vue
- **Utilisation**: Rapports exécutifs, prise de décision stratégique

## 🚀 Installation et déploiement

### Méthode 1: Script Python automatisé
```bash
cd c:\Users\hynco\Desktop\SIGETI_DWH
python create_kpi_views.py
```

### Méthode 2: Script SQL manuel
```bash
cd c:\Users\hynco\Desktop\SIGETI_DWH\sql_views
psql -h localhost -U postgres -d sigeti_dwh -f deploy_views.sql
```

### Méthode 3: Via Airflow (automatique)
Les vues sont automatiquement créées lors de l'exécution du pipeline `sigeti_etl_pipeline` dans Airflow.

## 🔍 Tests et validation

### Test complet des vues
```bash
python test_kpi_views.py --test
```

### Résumé exécutif uniquement
```bash
python test_kpi_views.py --summary
```

### Test manuel avec psql
```sql
-- Tester une vue spécifique
SELECT * FROM public.v_kpi_tableau_bord_executif;

-- Vérifier l'existence de toutes les vues
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE 'v_kpi_%';
```

## 📈 Exemples d'utilisation

### 1. Tableau de bord exécutif quotidien
```sql
SELECT 
    total_demandes,
    taux_acceptation_pct,
    delai_moyen_jours,
    statut_alerte
FROM public.v_kpi_tableau_bord_executif;
```

### 2. Analyse des délais par tranche
```sql
SELECT 
    delai_moyen_jours,
    demandes_sous_7j,
    demandes_8_15j,
    demandes_plus_15j
FROM public.v_kpi_delai_traitement;
```

### 3. Evolution mensuelle
```sql
SELECT 
    periode_mois,
    demandes_creees,
    taux_acceptation_mensuel,
    montant_finance
FROM public.v_kpi_analyse_temporelle
ORDER BY periode_mois DESC
LIMIT 12;  -- 12 derniers mois
```

### 4. Top 5 des zones les plus actives
```sql
SELECT 
    zone_industrielle,
    region,
    total_demandes,
    taux_acceptation_zone
FROM public.v_kpi_repartition_geographique
ORDER BY total_demandes DESC
LIMIT 5;
```

## 🔧 Maintenance

### Actualisation des vues
Les vues sont automatiquement actualisées à chaque exécution du pipeline ETL, car elles interrogent directement les tables de faits et dimensions.

### Modification des seuils d'alerte
Pour modifier les seuils d'alerte dans `v_kpi_tableau_bord_executif`, éditez le fichier `create_kpi_views.py`:

```python
# Exemple: Modifier le seuil d'acceptation de 30% à 25%
CASE 
    WHEN ROUND((SUM(nb_demandes_acceptees) * 100.0) / NULLIF(SUM(nb_demandes_finalisees), 0), 2) < 25 
    THEN 'ALERTE: Taux acceptation faible'
    ...
END as statut_alerte
```

### Ajout de nouvelles vues
1. Ajouter la définition SQL dans `VIEWS_SQL` du fichier `create_kpi_views.py`
2. Ajouter le test correspondant dans `test_kpi_views.py`
3. Re-déployer avec `python create_kpi_views.py`

## 📊 Intégration avec les outils BI

### Power BI
```sql
-- Connexion directe aux vues
Server: localhost
Database: sigeti_dwh
Tables: public.v_kpi_*
```

### Grafana
```sql
-- Exemple de requête pour Grafana
SELECT 
    date_calcul as time,
    taux_acceptation_pct as value,
    'Taux d''acceptation' as metric
FROM public.v_kpi_taux_acceptation
```

### Excel / Tableau
Connectez-vous directement à PostgreSQL et importez les vues comme sources de données.

## 🚨 Alertes et monitoring

### Seuils par défaut
- **Taux d'acceptation**: < 30% = Alerte
- **Délai de traitement**: > 15 jours = Alerte
- **Données manquantes**: NULL values = Alerte

### Configuration des notifications
Les alertes sont intégrées dans le pipeline Airflow (`sigeti_kpi_monitoring`) et peuvent être configurées pour envoyer des emails automatiques.

## 📝 Logs et debugging

### Fichiers de log
- Pipeline Airflow: `c:\Users\hynco\Desktop\SIGETI_DWH\airflow\logs\`
- Rapports KPI quotidiens: `kpi_report_YYYYMMDD.txt`

### Diagnostic des erreurs
```sql
-- Vérifier la disponibilité des données sources
SELECT COUNT(*) FROM marts.fct_demandes_attribution;
SELECT COUNT(*) FROM marts.dim_zones_industrielles;

-- Vérifier les permissions
SELECT has_table_privilege('public', 'marts.fct_demandes_attribution', 'select');
```

## 🔄 Cycle de mise à jour

1. **06:00** - Pipeline ETL principal (`sigeti_etl_pipeline`)
2. **08:00** - Monitoring KPI (`sigeti_kpi_monitoring`)
3. **Temps réel** - Actualisation automatique des vues lors des requêtes

## 📞 Support

Pour toute question ou problème:
1. Vérifier les logs Airflow
2. Exécuter `python test_kpi_views.py --test`
3. Consulter la documentation technique du projet SIGETI DWH