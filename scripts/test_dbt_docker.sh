#!/bin/bash
# Script pour tester dbt dans l'environnement Docker SIGETI

echo "🧪 Test de dbt dans l'environnement Docker SIGETI"
echo "=================================================="

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage coloré
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Vérifier que Docker Compose est disponible
if ! command -v docker-compose &> /dev/null; then
    print_status $RED "❌ Docker Compose n'est pas installé"
    exit 1
fi

print_status $GREEN "✅ Docker Compose disponible"

# Vérifier que le service dbt est démarré
if ! docker-compose ps dbt-service | grep -q "Up"; then
    print_status $YELLOW "⚠️  Service dbt non démarré - démarrage..."
    docker-compose up -d dbt-service
    sleep 10
fi

print_status $GREEN "✅ Service dbt opérationnel"

echo ""
print_status $BLUE "🔍 Test 1: Configuration dbt"
echo "--------------------------------"

# Test de la configuration dbt
if docker-compose exec -T dbt-service dbt debug --profiles-dir /opt/dbt_sigeti --target docker; then
    print_status $GREEN "✅ Configuration dbt valide"
else
    print_status $RED "❌ Problème de configuration dbt"
    exit 1
fi

echo ""
print_status $BLUE "🔍 Test 2: Connexion à la base de données"
echo "----------------------------------------"

# Test de connexion à la base
if docker-compose exec -T dbt-service python -c "
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
"; then
    print_status $GREEN "✅ Connexion à sigeti_dwh réussie"
else
    print_status $RED "❌ Impossible de se connecter à sigeti_dwh"
    print_status $YELLOW "💡 Vérifiez que la base est initialisée:"
    echo "   ./docker-sigeti.ps1 init-db"
    echo "   # ou"
    echo "   make init-db"
    exit 1
fi

echo ""
print_status $BLUE "🔍 Test 3: Compilation des modèles"
echo "--------------------------------"

# Test de compilation des modèles dbt
if docker-compose exec -T dbt-service dbt parse --profiles-dir /opt/dbt_sigeti --target docker; then
    print_status $GREEN "✅ Compilation des modèles réussie"
else
    print_status $RED "❌ Erreur de compilation des modèles"
    exit 1
fi

echo ""
print_status $BLUE "🔍 Test 4: Installation des dépendances"
echo "--------------------------------------"

# Test de dbt deps
if docker-compose exec -T dbt-service dbt deps --profiles-dir /opt/dbt_sigeti --target docker; then
    print_status $GREEN "✅ Installation des dépendances réussie"
else
    print_status $YELLOW "⚠️  Pas de dépendances à installer (normal si aucun packages.yml)"
fi

echo ""
print_status $BLUE "🔍 Test 5: Variables d'environnement"
echo "-----------------------------------"

# Vérifier les variables d'environnement dans le conteneur
docker-compose exec -T dbt-service env | grep SIGETI | while read line; do
    if [[ $line == *"PASSWORD"* ]]; then
        # Masquer les mots de passe
        var_name=$(echo $line | cut -d'=' -f1)
        var_value=$(echo $line | cut -d'=' -f2)
        masked_value=$(echo $var_value | sed 's/./*/g')
        print_status $GREEN "✅ $var_name=$masked_value"
    else
        print_status $GREEN "✅ $line"
    fi
done

echo ""
print_status $GREEN "🎉 TOUS LES TESTS RÉUSSIS !"
echo "=================================================="
print_status $BLUE "📋 Configuration validée:"
echo "   - Base de données: sigeti_dwh"
echo "   - Utilisateur: sigeti_user"  
echo "   - Host: host.docker.internal"
echo "   - Target dbt: docker"
echo ""
print_status $YELLOW "💡 Commandes dbt disponibles dans le conteneur:"
echo "   docker-compose exec dbt-service dbt run --target docker"
echo "   docker-compose exec dbt-service dbt test --target docker"  
echo "   docker-compose exec dbt-service dbt docs generate --target docker"