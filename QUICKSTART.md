# 🚀 SIGETI DWH Docker - Démarrage Rapide

## Installation initiale complète
```powershell
# Installation automatique complète
.\install-docker.ps1

# Installation en mode développement
.\install-docker.ps1 -DevMode

# Installation forcée (recréation configs)
.\install-docker.ps1 -Force
```

## Utilisation quotidienne  
```powershell
# Démarrer tous les services
.\docker-sigeti.ps1 up

# Voir le statut
.\docker-sigeti.ps1 status

# Voir les logs en temps réel
.\docker-sigeti.ps1 logs

# Arrêter proprement
.\docker-sigeti.ps1 down
```

## URLs importantes
- **Airflow** : http://localhost:8080 (admin/admin123)
- **Grafana** : http://localhost:3000 (admin/admin123)

## Dépannage rapide
```powershell
# Redémarrage complet
.\docker-sigeti.ps1 restart

# Test connexion DB
.\docker-sigeti.ps1 test-db-connection

# Nettoyage complet si problème
.\docker-sigeti.ps1 clean
.\docker-sigeti.ps1 build
.\docker-sigeti.ps1 up
```

## Documentation complète
📖 Voir `DOCKER_README.md` pour tous les détails