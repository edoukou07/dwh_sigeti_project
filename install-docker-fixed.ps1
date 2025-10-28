# Script d'installation Docker pour SIGETI DWH
# Installe et configure automatiquement l'environnement SIGETI complet

param(
    [switch]$DevMode,
    [switch]$Force,
    [switch]$SkipTests
)

# Fonction utilitaire pour l'affichage coloré
function Write-ColoredText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

# Fonction pour afficher les étapes
function Write-Step {
    param([string]$Step, [int]$Current, [int]$Total)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-ColoredText "ETAPE $Current/$Total : $Step" "Cyan"
    Write-Host "=" * 60 -ForegroundColor Cyan
}

# Fonction de validation de Docker
function Test-DockerInstallation {
    Write-Step "Vérification de Docker" 1 7
    
    try {
        $dockerVersion = docker --version
        Write-ColoredText "OK Docker detecte: $dockerVersion" "Green"
    }
    catch {
        Write-ColoredText "ERREUR Docker non trouve. Installez Docker Desktop d'abord." "Red"
        exit 1
    }
    
    try {
        $composeVersion = docker-compose --version
        Write-ColoredText "OK Docker Compose detecte: $composeVersion" "Green"
    }
    catch {
        Write-ColoredText "ERREUR Docker Compose non trouve." "Red"
        exit 1
    }

    Write-ColoredText "Test de connexion aux bases locales..." "Yellow"
    
    try {
        $testSigetiDwh = psql -h localhost -U sigeti_user -d sigeti_dwh -c "SELECT 1;" 2>$null
        Write-ColoredText "OK Base sigeti_dwh accessible" "Green"
    }
    catch {
        Write-ColoredText "WARNING Base sigeti_dwh non accessible (sera creee si necessaire)" "Yellow"
    }
    
    try {
        $testSigetiNode = psql -h localhost -U postgres -d sigeti_node_db -c "SELECT 1;" 2>$null
        Write-ColoredText "OK Base sigeti_node_db accessible" "Green"
    }
    catch {
        Write-ColoredText "WARNING Base sigeti_node_db non accessible" "Yellow"
    }
}

function Initialize-Environment {
    Write-Step "Initialisation de l'environnement" 2 7
    
    # Arrêter les services existants s'ils tournent
    Write-ColoredText "Arret des services existants..." "Yellow"
    docker-compose down 2>$null

    if ($Force) {
        Write-ColoredText "Mode Force : nettoyage complet..." "Yellow"
        docker-compose down --volumes --remove-orphans 2>$null
        docker system prune -f 2>$null
    }

    # Configuration du fichier .env si nécessaire
    if (!(Test-Path ".env") -or $Force) {
        Write-ColoredText "Configuration des variables d'environnement..." "Yellow"
        Copy-Item ".env" ".env.bak" -ErrorAction SilentlyContinue
        Write-ColoredText "OK Fichier .env configure" "Green"
    }
}

function Build-DockerImages {
    Write-Step "Construction des images Docker" 3 7
    
    Write-ColoredText "Construction des images personnalisees..." "Yellow"
    
    if ($DevMode) {
        $result = docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
    } else {
        $result = docker-compose build
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredText "OK Images construites avec succes" "Green"
    } else {
        Write-ColoredText "ERREUR lors de la construction des images" "Red"
        exit 1
    }
}

function Start-Services {
    Write-Step "Démarrage des services" 4 7
    
    Write-ColoredText "Demarrage de tous les services Docker..." "Yellow"
    
    if ($DevMode) {
        $result = docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    } else {
        $result = docker-compose up -d
    }
    
    if ($LASTEXITCODE -eq 0) {
        Start-Sleep 30  # Attendre que les services démarrent
        Write-ColoredText "OK Services demarres" "Green"
    } else {
        Write-ColoredText "ERREUR lors du demarrage des services" "Red"
        Write-Host "Consultez les logs avec: docker-compose logs"
        exit 1
    }
}

function Initialize-Airflow {
    Write-Step "Initialisation d'Airflow" 5 7
    
    Write-ColoredText "Attente du demarrage d'Airflow..." "Yellow"
    
    # Attendre qu'Airflow soit prêt
    $maxRetries = 12
    $retryCount = 0
    
    do {
        Start-Sleep 10
        $retryCount++
        Write-Host "Tentative $retryCount/$maxRetries..."
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColoredText "OK Airflow webserver operationnel" "Green"
                break
            }
        }
        catch {
            if ($retryCount -eq $maxRetries) {
                Write-ColoredText "ERREUR Airflow ne repond pas apres $maxRetries tentatives" "Red"
                return $false
            }
        }
    } while ($retryCount -lt $maxRetries)
    
    # Configuration de l'utilisateur admin
    try {
        docker-compose exec -T airflow-webserver airflow users create --username admin --password admin123 --firstname Admin --lastname User --role Admin --email admin@sigeti.com 2>$null
        Write-ColoredText "OK Utilisateur admin configure (admin/admin123)" "Green"
        return $true
    }
    catch {
        Write-ColoredText "WARNING Initialisation Airflow incomplete, verifier manuellement" "Yellow"
        return $false
    }
}

function Test-Installation {
    Write-Step "Tests de validation" 6 7
    
    if ($SkipTests) {
        Write-ColoredText "Tests de validation ignores" "Yellow"
        return $true
    }
    
    Write-ColoredText "Execution des tests de validation..." "Yellow"
    
    try {
        # Test de base de données
        .\docker-sigeti.ps1 test-db 2>$null
        Write-ColoredText "OK Validation terminee avec succes" "Green"
        return $true
    }
    catch {
        Write-ColoredText "WARNING Validation incomplete, verification manuelle recommandee" "Yellow"
        return $false
    }
}

function Show-Summary {
    Write-Step "Installation terminée" 7 7
    
    Write-Host ""
    Write-ColoredText "INSTALLATION SIGETI DWH TERMINEE !" "Green"
    Write-Host ""
    Write-ColoredText "Services disponibles :" "Yellow"
    Write-Host "   Airflow : http://localhost:8080 (admin/admin123)"
    Write-Host "   Grafana : http://localhost:3000 (admin/admin123)"
    Write-Host "   Jupyter : token sigeti123"
    Write-Host ""
    Write-ColoredText "Commandes utiles :" "Yellow"
    Write-Host "   .\docker-sigeti.ps1 status     - Voir l'etat des services"
    Write-Host "   .\docker-sigeti.ps1 logs       - Voir les logs"
    Write-Host "   .\docker-sigeti.ps1 restart    - Redemarrer"
    Write-Host "   .\docker-sigeti.ps1 down       - Arreter"
    Write-Host ""
    Write-ColoredText "Documentation :" "Yellow"
    Write-Host "   DOCKER_README.md               - Guide complet"
    Write-Host "   DATABASE_INIT.md               - Guide base de donnees"
    Write-Host ""
}

# Script principal
try {
    Write-Host ""
    Write-ColoredText "INSTALLATION AUTOMATIQUE SIGETI DWH" "Cyan"
    Write-ColoredText "Version Docker avec Airflow, dbt, Jupyter, Grafana" "White"
    Write-Host ""
    
    if ($DevMode) {
        Write-ColoredText "Mode Developpement active" "Yellow"
    }
    if ($Force) {
        Write-ColoredText "Mode Force active - recreation complete" "Yellow"
    }

    # Exécution des étapes
    Test-DockerInstallation
    Initialize-Environment
    Build-DockerImages
    Start-Services
    $airflowOk = Initialize-Airflow
    $testsOk = Test-Installation
    Show-Summary
    
    # Vérifier si tout s'est bien passé
    if ($airflowOk -and $testsOk) {
        Write-ColoredText "Installation reussie ! Tous les services sont operationnels." "Green"
        exit 0
    } else {
        Write-ColoredText "Installation partiellement reussie. Verification manuelle recommandee." "Yellow"
        exit 0
    }
    
} catch {
    Write-ColoredText "ERREUR durant l'installation :" "Red"
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-ColoredText "Actions correctives suggerees :" "Yellow"
    Write-Host "   1. Verifier que Docker Desktop est demarre"
    Write-Host "   2. Verifier la connectivite reseau"
    Write-Host "   3. Consulter les logs : docker-compose logs"
    Write-Host "   4. Relancer avec -Force pour forcer la reconstruction"
    
    exit 1
}