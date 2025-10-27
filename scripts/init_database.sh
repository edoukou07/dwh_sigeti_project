#!/bin/bash

# Script d'initialisation SIGETI DWH pour environnement Docker
# Crée automatiquement la base de données et l'utilisateur si nécessaire

set -e  # Arrêt en cas d'erreur

# Configuration depuis les variables d'environnement
ADMIN_HOST="${SIGETI_NODE_DB_HOST:-host.docker.internal}"
ADMIN_PORT="${SIGETI_NODE_DB_PORT:-5432}"
ADMIN_USER="${SIGETI_NODE_DB_USER:-postgres}"
ADMIN_PASSWORD="${SIGETI_NODE_DB_PASSWORD:-postgres}"

TARGET_DB="${SIGETI_DB_NAME:-sigeti_dwh}"
TARGET_USER="${SIGETI_DB_USER:-sigeti_user}"
TARGET_PASSWORD="${SIGETI_DB_PASSWORD:-sigeti123}"

echo "🐳 SIGETI DWH - Initialisation Base de Données"
echo "=============================================="
echo "🏗️  Host: $ADMIN_HOST:$ADMIN_PORT"
echo "🗄️  Base cible: $TARGET_DB"
echo "👤 Utilisateur cible: $TARGET_USER"
echo ""

# Fonction de test de connexion
test_connection() {
    local host=$1
    local port=$2
    local user=$3
    local password=$4
    local database=${5:-postgres}
    
    PGPASSWORD=$password psql -h $host -p $port -U $user -d $database -c "SELECT 1;" > /dev/null 2>&1
}

# Test de connexion admin
echo "🔍 Test de connexion administrateur..."
if test_connection $ADMIN_HOST $ADMIN_PORT $ADMIN_USER $ADMIN_PASSWORD; then
    echo "✅ Connexion admin OK"
else
    echo "❌ Impossible de se connecter en tant qu'admin"
    echo "Vérifiez que PostgreSQL est démarré et accessible"
    exit 1
fi

# Vérifier si l'utilisateur existe
echo "👤 Vérification de l'utilisateur $TARGET_USER..."
USER_EXISTS=$(PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d postgres -tAc "SELECT 1 FROM pg_user WHERE usename='$TARGET_USER';" 2>/dev/null || echo "")

if [ -z "$USER_EXISTS" ]; then
    echo "🔨 Création de l'utilisateur $TARGET_USER..."
    PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d postgres -c "
        CREATE USER $TARGET_USER 
        WITH PASSWORD '$TARGET_PASSWORD' 
        CREATEDB 
        LOGIN;
    "
    echo "✅ Utilisateur $TARGET_USER créé"
else
    echo "👤 Utilisateur $TARGET_USER existe déjà"
fi

# Vérifier si la base existe
echo "🗄️  Vérification de la base $TARGET_DB..."
DB_EXISTS=$(PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$TARGET_DB';" 2>/dev/null || echo "")

if [ -z "$DB_EXISTS" ]; then
    echo "🔨 Création de la base $TARGET_DB..."
    PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d postgres -c "
        CREATE DATABASE $TARGET_DB 
        WITH OWNER = $TARGET_USER
        ENCODING = 'UTF8'
        TEMPLATE = template0;
    "
    echo "✅ Base $TARGET_DB créée"
else
    echo "🗄️  Base $TARGET_DB existe déjà"
fi

# Accorder les permissions sur la base
echo "🔐 Configuration des permissions..."
PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d postgres -c "
    GRANT ALL PRIVILEGES ON DATABASE $TARGET_DB TO $TARGET_USER;
"

# Configuration de la structure dans la base cible
echo "🏗️  Configuration de la structure de base..."
PGPASSWORD=$ADMIN_PASSWORD psql -h $ADMIN_HOST -p $ADMIN_PORT -U $ADMIN_USER -d $TARGET_DB -c "

-- Créer les extensions nécessaires (ignorer les erreurs si déjà installées)
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"btree_gin\";
CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";

-- Créer les schémas de base
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS reporting;

-- Accorder les permissions sur les schémas
GRANT ALL ON SCHEMA public TO $TARGET_USER;
GRANT ALL ON SCHEMA staging TO $TARGET_USER;
GRANT ALL ON SCHEMA dwh TO $TARGET_USER;
GRANT ALL ON SCHEMA reporting TO $TARGET_USER;

-- Permissions par défaut pour les futures tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $TARGET_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO $TARGET_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA dwh GRANT ALL ON TABLES TO $TARGET_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA reporting GRANT ALL ON TABLES TO $TARGET_USER;

-- Permissions sur les séquences
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO $TARGET_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $TARGET_USER;

-- Table de configuration système
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration initiale
INSERT INTO system_config (config_key, config_value, description) 
VALUES 
    ('db_version', '1.0.0', 'Version de la structure de base de données'),
    ('initialized_at', CURRENT_TIMESTAMP::TEXT, 'Date d''initialisation de la base'),
    ('environment', 'docker', 'Environnement d''exécution')
ON CONFLICT (config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Permissions sur system_config
GRANT ALL ON system_config TO $TARGET_USER;
GRANT ALL ON system_config_id_seq TO $TARGET_USER;

"

# Test de connexion final avec l'utilisateur créé
echo "🧪 Test de connexion final avec l'utilisateur $TARGET_USER..."
if test_connection $ADMIN_HOST $ADMIN_PORT $TARGET_USER $TARGET_PASSWORD $TARGET_DB; then
    echo "✅ Test de connexion utilisateur OK"
else
    echo "⚠️  Problème de connexion utilisateur (peut être normal)"
fi

# Affichage du résumé
echo ""
echo "🎉 Initialisation terminée avec succès!"
echo "📋 Résumé:"
echo "   Base: $TARGET_DB"
echo "   Utilisateur: $TARGET_USER"
echo "   Schémas: public, staging, dwh, reporting"
echo "   Extensions: uuid-ossp, btree_gin, pg_trgm"
echo ""
echo "✅ SIGETI DWH prêt pour l'ETL!"