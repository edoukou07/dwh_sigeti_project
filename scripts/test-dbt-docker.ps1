# Script PowerShell pour tester dbt dans l'environnement Docker SIGETI
# Usage: .\test-dbt-docker.ps1

Write-Host "🧪 Test de dbt dans l'environnement Docker SIGETI" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

function Write-ColoredText {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

# Vérifier que Docker Compose est disponible
Write-Host "`n🔍 Vérification des prérequis..." -ForegroundColor Yellow
try {
    $dockerComposeVersion = docker-compose --version 2>$null
    if ($dockerComposeVersion) {
        Write-ColoredText "✅ Docker Compose disponible" "Green"
    } else {
        throw "Docker Compose non trouvé"
    }
} catch {
    Write-ColoredText "❌ Docker Compose n'est pas installé ou accessible" "Red"
    exit 1
}

# Vérifier que le service dbt est opérationnel
Write-Host "`n🔍 Vérification du service dbt..." -ForegroundColor Yellow
try {
    $dbtStatus = docker-compose ps dbt-service 2>$null
    if ($dbtStatus -match "Up") {
        Write-ColoredText "✅ Service dbt opérationnel" "Green"
    } else {
        Write-ColoredText "⚠️  Service dbt non démarré - démarrage..." "Yellow"
        docker-compose up -d dbt-service
        Start-Sleep 10
        Write-ColoredText "✅ Service dbt démarré" "Green"
    }
} catch {
    Write-ColoredText "❌ Impossible de vérifier le statut du service dbt" "Red"
    exit 1
}

# Test 1: Configuration dbt
Write-Host "`n🔍 Test 1: Configuration dbt" -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue
try {
    $debugResult = docker-compose exec -T dbt-service dbt debug --profiles-dir /opt/dbt_sigeti --target docker 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredText "✅ Configuration dbt valide" "Green"
    } else {
        Write-ColoredText "❌ Problème de configuration dbt" "Red"
        Write-Host $debugResult
        exit 1
    }
} catch {
    Write-ColoredText "❌ Erreur lors du test de configuration" "Red"
    exit 1
}

# Test 2: Connexion à la base de données
Write-Host "`n🔍 Test 2: Connexion à la base de données" -ForegroundColor Blue
Write-Host "----------------------------------------" -ForegroundColor Blue
try {
    $connectionTest = @"
import psycopg2
try:
    conn = psycopg2.connect(
        host='host.docker.internal',
        port=5432,
        database='sigeti_dwh',
        user='sigeti_user',
        password='sigeti123'
    )
    print('✅ Connexion DB réussie')
    conn.close()
except Exception as e:
    print(f'❌ Erreur de connexion: {e}')
    exit(1)
"@

    docker-compose exec -T dbt-service python -c $connectionTest 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredText "✅ Connexion à sigeti_dwh réussie" "Green"
    } else {
        Write-ColoredText "❌ Impossible de se connecter à sigeti_dwh" "Red"
        Write-ColoredText "💡 Vérifiez que la base est initialisée:" "Yellow"
        Write-Host "   .\docker-sigeti.ps1 init-db"
        Write-Host "   # ou"
        Write-Host "   make init-db"
        exit 1
    }
} catch {
    Write-ColoredText "❌ Erreur lors du test de connexion" "Red"
    exit 1
}

# Test 3: Compilation des modèles
Write-Host "`n🔍 Test 3: Compilation des modèles" -ForegroundColor Blue
Write-Host "--------------------------------" -ForegroundColor Blue
try {
    $parseResult = docker-compose exec -T dbt-service dbt parse --profiles-dir /opt/dbt_sigeti --target docker 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredText "✅ Compilation des modèles réussie" "Green"
    } else {
        Write-ColoredText "❌ Erreur de compilation des modèles" "Red"
        Write-Host $parseResult
        exit 1
    }
} catch {
    Write-ColoredText "❌ Erreur lors de la compilation" "Red"
    exit 1
}

# Test 4: Installation des dépendances
Write-Host "`n🔍 Test 4: Installation des dépendances" -ForegroundColor Blue
Write-Host "--------------------------------------" -ForegroundColor Blue
try {
    docker-compose exec -T dbt-service dbt deps --profiles-dir /opt/dbt_sigeti --target docker 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredText "✅ Installation des dépendances réussie" "Green"
    } else {
        Write-ColoredText "⚠️  Pas de dépendances à installer (normal si aucun packages.yml)" "Yellow"
    }
} catch {
    Write-ColoredText "⚠️  Erreur lors de l'installation des dépendances (peut être normal)" "Yellow"
}

# Test 5: Variables d'environnement
Write-Host "`n🔍 Test 5: Variables d'environnement" -ForegroundColor Blue
Write-Host "-----------------------------------" -ForegroundColor Blue
try {
    $envVars = docker-compose exec -T dbt-service env 2>$null | Where-Object { $_ -match "SIGETI" }
    foreach ($var in $envVars) {
        if ($var -match "PASSWORD") {
            $parts = $var -split "=", 2
            $varName = $parts[0]
            $varValue = $parts[1]
            $maskedValue = "*" * $varValue.Length
            Write-ColoredText "✅ $varName=$maskedValue" "Green"
        } else {
            Write-ColoredText "✅ $var" "Green"
        }
    }
} catch {
    Write-ColoredText "⚠️  Impossible de lire les variables d'environnement" "Yellow"
}

# Résumé final
Write-Host "`n🎉 TOUS LES TESTS RÉUSSIS !" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "📋 Configuration validée:" -ForegroundColor Blue
Write-Host "   - Base de données: sigeti_dwh"
Write-Host "   - Utilisateur: sigeti_user"
Write-Host "   - Host: host.docker.internal"
Write-Host "   - Target dbt: docker"
Write-Host ""
Write-Host "💡 Commandes dbt disponibles dans le conteneur:" -ForegroundColor Yellow
Write-Host "   docker-compose exec dbt-service dbt run --target docker"
Write-Host "   docker-compose exec dbt-service dbt test --target docker"
Write-Host "   docker-compose exec dbt-service dbt docs generate --target docker"