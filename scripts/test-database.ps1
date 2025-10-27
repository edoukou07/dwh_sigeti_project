# Script PowerShell pour tester l'initialisation de la base de données SIGETI
# Usage: .\test-database.ps1

param(
    [string]$DbHost = "localhost",
    [string]$Port = "5432",
    [string]$AdminUser = "postgres",
    [string]$AdminPassword = "postgres",
    [string]$SigetiDb = "sigeti_dwh",
    [string]$SigetiUser = "sigeti_user",
    [string]$SigetiPassword = "sigeti123"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "🧪 TESTS D'INITIALISATION BASE DE DONNÉES SIGETI" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration des variables d'environnement
$env:SIGETI_NODE_HOST = $DbHost
$env:SIGETI_NODE_PORT = $Port
$env:SIGETI_NODE_USER = $AdminUser
$env:SIGETI_NODE_PASSWORD = $AdminPassword
$env:SIGETI_SIGETI_DB = $SigetiDb
$env:SIGETI_SIGETI_USER = $SigetiUser
$env:SIGETI_SIGETI_PASSWORD = $SigetiPassword

Write-Host "`n📋 Configuration des tests:" -ForegroundColor Yellow
Write-Host "  Host: $DbHost" -ForegroundColor White
Write-Host "  Port: $Port" -ForegroundColor White
Write-Host "  Admin User: $AdminUser" -ForegroundColor White
Write-Host "  Admin Password: $('*' * $AdminPassword.Length)" -ForegroundColor White
Write-Host "  SIGETI DB: $SigetiDb" -ForegroundColor White
Write-Host "  SIGETI User: $SigetiUser" -ForegroundColor White
Write-Host "  SIGETI Password: $('*' * $SigetiPassword.Length)" -ForegroundColor White

# Vérifier si Python est disponible
Write-Host "`n🔍 Vérification de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python trouvé: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python non trouvé. Veuillez installer Python." -ForegroundColor Red
    exit 1
}

# Vérifier si psycopg2 est installé
Write-Host "`n🔍 Vérification des dépendances Python..." -ForegroundColor Yellow
try {
    python -c "import psycopg2" 2>$null
    Write-Host "✅ psycopg2 disponible" -ForegroundColor Green
} catch {
    Write-Host "⚠️  psycopg2 non trouvé. Installation..." -ForegroundColor Yellow
    try {
        pip install psycopg2-binary
        Write-Host "✅ psycopg2-binary installé" -ForegroundColor Green
    } catch {
        Write-Host "❌ Impossible d'installer psycopg2-binary" -ForegroundColor Red
        Write-Host "💡 Essayez: pip install psycopg2-binary" -ForegroundColor Yellow
        exit 1
    }
}

# Exécuter le script de test Python
Write-Host "`n🚀 Lancement des tests..." -ForegroundColor Yellow
$scriptPath = Join-Path $PSScriptRoot "test_database_init.py"

if (Test-Path $scriptPath) {
    try {
        python $scriptPath
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "`n🎉 Tests terminés avec succès!" -ForegroundColor Green
            Write-Host "🚀 La base de données est prête pour le pipeline SIGETI" -ForegroundColor Green
        } else {
            Write-Host "`n❌ Certains tests ont échoué (Code de sortie: $exitCode)" -ForegroundColor Red
            Write-Host "🔧 Consultez les logs ci-dessus pour plus de détails" -ForegroundColor Yellow
        }
        
        exit $exitCode
    } catch {
        Write-Host "`n❌ Erreur lors de l'exécution des tests: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n❌ Script de test non trouvé: $scriptPath" -ForegroundColor Red
    Write-Host "💡 Assurez-vous que le fichier test_database_init.py existe dans le dossier scripts" -ForegroundColor Yellow
    exit 1
}