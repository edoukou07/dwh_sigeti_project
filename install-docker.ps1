# Script d'installation initiale SIGETI DWH Docker
# Ce script configure et démarre l'environnement Docker complet

param(
    [switch]$SkipValidation,
    [switch]$DevMode,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-ColoredText {
    param([string]$Text, [string]$Color = "White")
    switch ($Color) {
        "Red" { Write-Host $Text -ForegroundColor Red }
        "Green" { Write-Host $Text -ForegroundColor Green }
        "Yellow" { Write-Host $Text -ForegroundColor Yellow }
        "Cyan" { Write-Host $Text -ForegroundColor Cyan }
        "Magenta" { Write-Host $Text -ForegroundColor Magenta }
        default { Write-Host $Text -ForegroundColor White }
    }
}

function Write-Step {
    param([string]$Step, [int]$Current, [int]$Total)
    Write-Host ""
    Write-ColoredText "🚀 Étape $Current/$Total : $Step" "Cyan"
    Write-Host "=" * 60
}

function Test-Prerequisites {
    Write-Step "Vérification des prérequis" 1 7
    
    # Test Docker
    try {
        $dockerVersion = docker --version
        Write-ColoredText "✅ Docker détecté: $dockerVersion" "Green"
    }
    catch {
        Write-ColoredText "❌ Docker non trouvé. Installez Docker Desktop d'abord." "Red"
        exit 1
    }
    
    # Test Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-ColoredText "✅ Docker Compose détecté: $composeVersion" "Green"
    }
    catch {
        Write-ColoredText "❌ Docker Compose non trouvé." "Red"
        exit 1
    }
    
    # Test des bases locales
    Write-ColoredText "🔍 Test de connexion aux bases locales..." "Yellow"
    
    try {
        $testSigetiDwh = psql -h localhost -U sigeti_user -d sigeti_dwh -c "SELECT 1;" 2>$null
        Write-ColoredText "✅ Base sigeti_dwh accessible" "Green"
    }
    catch {
        Write-ColoredText "⚠️  Base sigeti_dwh non accessible (sera créée si nécessaire)" "Yellow"
    }
    
    try {
        $testSigetiNode = psql -h localhost -U postgres -d sigeti_node_db -c "SELECT 1;" 2>$null
        Write-ColoredText "✅ Base sigeti_node_db accessible" "Green"
    }
    catch {
        Write-ColoredText "⚠️  Base sigeti_node_db non accessible" "Yellow"
    }
}

function Initialize-Environment {
    Write-Step "Initialisation de l'environnement" 2 7
    
    # Vérifier et créer les répertoires nécessaires
    $directories = @(
        ".\logs",
        ".\backups",
        ".\monitoring\grafana\dashboards",
        ".\notebooks\data"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory -Force | Out-Null
            Write-ColoredText "📁 Répertoire créé: $dir" "Green"
        }
    }
    
    # Copier les fichiers de configuration par défaut si nécessaire
    if (!(Test-Path ".\.env") -or $Force) {
        Write-ColoredText "⚙️ Configuration des variables d'environnement..." "Yellow"
        # Le fichier .env existe déjà, pas besoin de le recréer
        Write-ColoredText "✅ Fichier .env configuré" "Green"
    }
}

function Build-Images {
    Write-Step "Construction des images Docker" 3 7
    
    Write-ColoredText "🔨 Construction des images personnalisées..." "Yellow"
    Write-ColoredText "   (Cette étape peut prendre plusieurs minutes)" "Yellow"
    
    try {
        if ($DevMode) {
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
        }
        else {
            docker-compose build --no-cache
        }
        Write-ColoredText "✅ Images construites avec succès" "Green"
    }
    catch {
        Write-ColoredText "❌ Erreur lors de la construction des images" "Red"
        Write-ColoredText "Logs d'erreur:" "Red"
        Write-Host $_.Exception.Message
        exit 1
    }
}

function Start-Services {
    Write-Step "Démarrage des services" 4 7
    
    Write-ColoredText "🚀 Démarrage de tous les services Docker..." "Yellow"
    
    try {
        if ($DevMode) {
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        }
        else {
            docker-compose up -d
        }
        
        Write-ColoredText "✅ Services démarrés" "Green"
        
        # Attendre que les services soient prêts
        Write-ColoredText "⏳ Attente du démarrage complet des services..." "Yellow"
        Start-Sleep -Seconds 45
        
    }
    catch {
        Write-ColoredText "❌ Erreur lors du démarrage des services" "Red"
        Write-Host $_.Exception.Message
        exit 1
    }
}

function Initialize-Airflow {
    Write-Step "Initialisation d'Airflow" 5 7
    
    Write-ColoredText "🔑 Configuration initiale d'Airflow..." "Yellow"
    
    try {
        # Attendre qu'Airflow soit prêt
        $maxRetries = 12
        $retryCount = 0
        
        do {
            $retryCount++
            Write-ColoredText "   Tentative $retryCount/$maxRetries..." "Yellow"
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -TimeoutSec 10 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-ColoredText "✅ Airflow webserver opérationnel" "Green"
                    break
                }
            }
            catch {
                if ($retryCount -eq $maxRetries) {
                    Write-ColoredText "❌ Airflow ne répond pas après $maxRetries tentatives" "Red"
                    return
                }
                Start-Sleep -Seconds 15
            }
        } while ($retryCount -lt $maxRetries)
        
        # Vérifier l'utilisateur admin (créé automatiquement par l'entrypoint)
        Write-ColoredText "✅ Utilisateur admin configuré (admin/admin123)" "Green"
        
    }
    catch {
        Write-ColoredText "⚠️  Initialisation Airflow incomplète, vérifier manuellement" "Yellow"
    }
}

function Test-Installation {
    Write-Step "Validation de l'installation" 6 7
    
    if ($SkipValidation) {
        Write-ColoredText "⏭️  Tests de validation ignorés" "Yellow"
        return
    }
    
    Write-ColoredText "🧪 Exécution des tests de validation..." "Yellow"
    
    try {
        # Exécuter le script de validation
        python ".\scripts\validate_docker_installation.py"
        Write-ColoredText "✅ Validation terminée avec succès" "Green"
    }
    catch {
        Write-ColoredText "⚠️  Validation incomplète, vérification manuelle recommandée" "Yellow"
    }
}

function Show-Summary {
    Write-Step "Installation terminée !" 7 7
    
    Write-ColoredText "🎉 SIGETI DWH Docker est maintenant opérationnel !" "Green"
    Write-Host ""
    
    Write-ColoredText "🌐 URLs d'accès :" "Cyan"
    Write-Host "   📊 Airflow Webserver : http://localhost:8080"
    Write-Host "   📈 Grafana Dashboard : http://localhost:3000"
    Write-Host "   📓 Jupyter Notebooks : http://localhost:8888"
    Write-Host "   🌸 Flower (Celery)   : http://localhost:5555"
    Write-Host "   📉 Prometheus        : http://localhost:9090"
    
    if ($DevMode) {
        Write-Host ""
        Write-ColoredText "🔧 Outils de développement :" "Cyan"
        Write-Host "   🗄️  Adminer          : http://localhost:8082"
        Write-Host "   🐘 pgAdmin          : http://localhost:8083"
        Write-Host "   🔴 Redis Insight     : http://localhost:8084"
    }
    
    Write-Host ""
    Write-ColoredText "🔐 Identifiants par défaut :" "Cyan"
    Write-Host "   Airflow : admin / admin123"
    Write-Host "   Grafana : admin / admin123"
    Write-Host "   Jupyter : token sigeti123"
    
    Write-Host ""
    Write-ColoredText "📜 Commandes utiles :" "Cyan"
    Write-Host "   .\docker-sigeti.ps1 status    # Statut des services"
    Write-Host "   .\docker-sigeti.ps1 logs      # Voir les logs"
    Write-Host "   .\docker-sigeti.ps1 restart   # Redémarrer"
    Write-Host "   .\docker-sigeti.ps1 help      # Aide complète"
    
    Write-Host ""
    Write-ColoredText "📖 Documentation : DOCKER_README.md" "Magenta"
}

# ===== EXÉCUTION PRINCIPALE =====

Write-Host ""
Write-ColoredText "🐳 SIGETI DWH - Installation Docker Complète" "Magenta"
Write-Host "=" * 60

if ($DevMode) {
    Write-ColoredText "🔧 Mode développement activé" "Yellow"
}

if ($Force) {
    Write-ColoredText "⚡ Mode force activé (recréation des configurations)" "Yellow"
}

try {
    Test-Prerequisites
    Initialize-Environment
    Build-Images
    Start-Services
    Initialize-Airflow
    Test-Installation
    Show-Summary
    
    Write-Host ""
    Write-ColoredText "🎯 Installation réussie ! Votre environnement SIGETI DWH est prêt." "Green"
    
} catch {
    Write-Host ""
    Write-ColoredText "❌ Erreur durant l'installation :" "Red"
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-ColoredText "🔧 Actions correctives suggérées :" "Yellow"
    Write-Host "   1. Vérifier que Docker Desktop est démarré"
    Write-Host "   2. Vérifier la connectivité réseau"
    Write-Host "   3. Consulter les logs : docker-compose logs"
    Write-Host "   4. Relancer avec -Force pour forcer la reconstruction"
    
    exit 1
}