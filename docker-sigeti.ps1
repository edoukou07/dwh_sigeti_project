# Script PowerShell pour gérer SIGETI DWH Docker
# Usage: .\docker-sigeti.ps1 <command>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("help", "build", "up", "down", "stop", "restart", "logs", "logs-airflow", "status", "clean", "clean-all", "airflow-up", "dbt-shell", "jupyter-up", "monitoring-up", "test-db", "test-kpi", "test-init", "init-db", "test-dbt", "test-dbt-docker", "run-etl", "dev", "init-airflow", "backup", "info")]
    [string]$Command
)

$ComposeFile = "docker-compose.yml"
$ProjectName = "sigeti_dwh"

function Write-ColoredText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Show-Help {
    Write-ColoredText "SIGETI DWH Docker - Commandes disponibles:" "Cyan"
    Write-Host ""
    Write-Host "  build                  Construction des conteneurs"
    Write-Host "  up                     Démarrer tous les services"
    Write-Host "  down                   Arrêter tous les services"
    Write-Host "  stop                   Pause des services"
    Write-Host "  restart                Redémarrer tous les services"
    Write-Host "  logs                   Voir les logs de tous les services"
    Write-Host "  logs-airflow          Voir les logs Airflow seulement"
    Write-Host "  status                 Voir le statut des services"
    Write-Host "  clean                  Nettoyer (volumes inclus)"
    Write-Host "  clean-all              Nettoyage complet + images"
    Write-Host ""
    Write-Host "Services individuels:"
    Write-Host "  airflow-up             Démarrer seulement Airflow"
    Write-Host "  dbt-shell              Accéder au shell dbt"
    Write-Host "  jupyter-up             Démarrer seulement Jupyter"
    Write-Host "  monitoring-up          Démarrer seulement le monitoring"
    Write-Host ""
    Write-Host "Tests et validation:"
    Write-Host "  test-db                Tester connexion DB locales"
    Write-Host "  test-kpi               Tester les KPI views"
    Write-Host "  test-init              Tester l'initialisation DB"
    Write-Host "  init-db                Initialiser la base manuellement"
    Write-Host "  test-dbt               Valider la configuration dbt"
    Write-Host "  test-dbt-docker        Tester dbt dans Docker"
    Write-Host "  run-etl                Exécuter l'ETL manuellement"
    Write-Host ""
    Write-Host "Utilitaires:"
    Write-Host "  dev                    Mode développement"
    Write-Host "  init-airflow           Initialiser Airflow"
    Write-Host "  backup                 Sauvegarde des volumes"
    Write-Host "  info                   Informations système"
}

function Show-Info {
    Write-ColoredText "SIGETI DWH Docker - Informations" "Yellow"
    Write-Host "===================================="
    Write-Host "Projet: $ProjectName"
    Write-Host "Compose: $ComposeFile"
    Write-Host ""
    Write-ColoredText "URLs d'accès:" "Green"
    Write-Host "   Airflow:    http://localhost:8080"
    Write-Host "   Grafana:    http://localhost:3000"
    Write-Host "   Jupyter:    http://localhost:8888"
    Write-Host "   Flower:     http://localhost:5555"
    Write-Host "   Prometheus: http://localhost:9090"
    Write-Host ""
    Write-ColoredText "Identifiants par défaut:" "Green"
    Write-Host "   Airflow:  admin / admin123"
    Write-Host "   Grafana:  admin / admin123"
    Write-Host "   Jupyter:  token sigeti123"
}

# Exécution des commandes
if ($Command -eq "help") {
    Show-Help
}
elseif ($Command -eq "build") {
    Write-ColoredText "Construction des images Docker..." "Yellow"
    docker-compose -f $ComposeFile build --no-cache
}
elseif ($Command -eq "up") {
    Write-ColoredText "Démarrage de SIGETI DWH..." "Green"
    docker-compose -f $ComposeFile up -d
    Write-ColoredText "Services démarrés!" "Green"
    Write-Host ""
    Write-ColoredText "Airflow: http://localhost:8080 (admin/admin123)" "Cyan"
    Write-ColoredText "Grafana: http://localhost:3000 (admin/admin123)" "Cyan"
    Write-ColoredText "Jupyter: http://localhost:8888 (token: sigeti123)" "Cyan"
    Write-ColoredText "Flower: http://localhost:5555" "Cyan"
}
elseif ($Command -eq "down") {
    Write-ColoredText "Arrêt des services..." "Yellow"
    docker-compose -f $ComposeFile down
}
elseif ($Command -eq "stop") {
    Write-ColoredText "Pause des services..." "Yellow"
    docker-compose -f $ComposeFile stop
}
elseif ($Command -eq "restart") {
    Write-ColoredText "Redémarrage des services..." "Yellow"
    docker-compose -f $ComposeFile down
    docker-compose -f $ComposeFile up -d
}
elseif ($Command -eq "logs") {
    docker-compose -f $ComposeFile logs -f
}
elseif ($Command -eq "logs-airflow") {
    docker-compose -f $ComposeFile logs -f airflow-webserver airflow-scheduler airflow-worker
}
elseif ($Command -eq "status") {
    Write-ColoredText "Statut des services SIGETI DWH:" "Cyan"
    docker-compose -f $ComposeFile ps
}
elseif ($Command -eq "clean") {
    Write-ColoredText "Nettoyage complet..." "Yellow"
    docker-compose -f $ComposeFile down -v --remove-orphans
    docker system prune -f
}
elseif ($Command -eq "clean-all") {
    Write-ColoredText "Nettoyage complet avec images..." "Red"
    docker-compose -f $ComposeFile down -v --remove-orphans
    docker system prune -af
}
elseif ($Command -eq "airflow-up") {
    Write-ColoredText "Démarrage Airflow..." "Green"
    docker-compose -f $ComposeFile up -d postgres-airflow redis airflow-webserver airflow-scheduler airflow-worker
}
elseif ($Command -eq "dbt-shell") {
    Write-ColoredText "Accès au shell dbt..." "Cyan"
    docker-compose -f $ComposeFile exec dbt-service bash
}
elseif ($Command -eq "jupyter-up") {
    Write-ColoredText "Démarrage Jupyter..." "Green"
    docker-compose -f $ComposeFile up -d jupyter
}
elseif ($Command -eq "monitoring-up") {
    Write-ColoredText "Démarrage monitoring..." "Green"
    docker-compose -f $ComposeFile up -d grafana prometheus
}
elseif ($Command -eq "test-db") {
    Write-ColoredText "Test de connexion aux bases locales..." "Yellow"
    $pythonCmd = 'import psycopg2; conn = psycopg2.connect(host="host.docker.internal", port=5432, database="sigeti_dwh", user="sigeti_user", password="sigeti123"); print("OK SIGETI DWH"); conn.close()'
    docker-compose -f $ComposeFile exec airflow-webserver python -c $pythonCmd
}
elseif ($Command -eq "test-kpi") {
    Write-ColoredText "Test des vues KPI..." "Yellow"
    docker-compose -f $ComposeFile exec dbt-service python /opt/airflow/scripts/create_kpi_views.py
}
elseif ($Command -eq "test-init") {
    Write-ColoredText "Test d'initialisation de la base..." "Yellow"
    & "$PSScriptRoot\scripts\test-database.ps1"
}
elseif ($Command -eq "init-db") {
    Write-ColoredText "Initialisation manuelle de la base..." "Yellow"
    python "$PSScriptRoot\scripts\init_database.py"
}
elseif ($Command -eq "test-dbt") {
    Write-ColoredText "Test de la configuration dbt..." "Yellow"
    python "$PSScriptRoot\scripts\validate_dbt_config.py"
}
elseif ($Command -eq "test-dbt-docker") {
    Write-ColoredText "Test dbt dans Docker..." "Yellow"
    & "$PSScriptRoot\scripts\test-dbt-docker.ps1"
}
elseif ($Command -eq "run-etl") {
    Write-ColoredText "Exécution ETL SIGETI..." "Yellow"
    docker-compose -f $ComposeFile exec airflow-worker python /opt/airflow/scripts/etl_sigeti.py
}
elseif ($Command -eq "dev") {
    Write-ColoredText "Mode développement..." "Yellow"
    docker-compose -f $ComposeFile up -d --build
}
elseif ($Command -eq "init-airflow") {
    Write-ColoredText "Initialisation Airflow..." "Yellow"
    docker-compose -f $ComposeFile exec airflow-webserver airflow db init
    docker-compose -f $ComposeFile exec airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@sigeti.local --password admin123
}
elseif ($Command -eq "backup") {
    Write-ColoredText "Sauvegarde des données..." "Yellow"
    $BackupDir = ".\backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -Path $BackupDir -ItemType Directory -Force | Out-Null
    $backupFile = "/backup/airflow_$(Get-Date -Format 'yyyyMMdd_HHmmss').tar.gz"
    docker run --rm -v sigeti_dwh_airflow_postgres_data:/data -v ${PWD}/backups:/backup alpine tar czf $backupFile -C /data .
}
elseif ($Command -eq "info") {
    Show-Info
}
else {
    Write-ColoredText "Commande inconnue: $Command" "Red"
    Show-Help
}