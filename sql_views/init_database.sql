-- Script SQL d'initialisation SIGETI DWH
-- Crée la base de données et l'utilisateur si ils n'existent pas
-- À exécuter en tant que superuser PostgreSQL (postgres)

-- Vérifier et créer l'utilisateur sigeti_user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'sigeti_user') THEN
        CREATE USER sigeti_user WITH 
            PASSWORD 'sigeti123'
            CREATEDB 
            LOGIN;
        RAISE NOTICE '✅ Utilisateur sigeti_user créé';
    ELSE
        RAISE NOTICE '👤 Utilisateur sigeti_user existe déjà';
    END IF;
END
$$;

-- Vérifier et créer la base de données sigeti_dwh
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sigeti_dwh') THEN
        -- Note: CREATE DATABASE ne peut pas être dans un bloc DO
        -- Cette partie doit être exécutée séparément
        RAISE NOTICE '🗄️  Base sigeti_dwh doit être créée manuellement';
    ELSE
        RAISE NOTICE '🗄️  Base sigeti_dwh existe déjà';
    END IF;
END
$$;

-- Créer la base sigeti_dwh si elle n'existe pas (à exécuter après le bloc précédent)
SELECT 'CREATE DATABASE sigeti_dwh WITH OWNER = sigeti_user ENCODING = ''UTF8'' TEMPLATE = template0'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sigeti_dwh')\gexec

-- Accorder les permissions sur la base
GRANT ALL PRIVILEGES ON DATABASE sigeti_dwh TO sigeti_user;

-- Script à exécuter DANS la base sigeti_dwh
\c sigeti_dwh

-- Créer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Créer les schémas de base
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS reporting;

-- Accorder les permissions sur les schémas
GRANT ALL ON SCHEMA public TO sigeti_user;
GRANT ALL ON SCHEMA staging TO sigeti_user;
GRANT ALL ON SCHEMA dwh TO sigeti_user;
GRANT ALL ON SCHEMA reporting TO sigeti_user;

-- Permissions par défaut pour les futures tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sigeti_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO sigeti_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA dwh GRANT ALL ON TABLES TO sigeti_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA reporting GRANT ALL ON TABLES TO sigeti_user;

-- Permissions sur les séquences
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO sigeti_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sigeti_user;

-- Créer une table de configuration système
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insérer la configuration initiale
INSERT INTO system_config (config_key, config_value, description) 
VALUES 
    ('db_version', '1.0.0', 'Version de la structure de base de données'),
    ('initialized_at', CURRENT_TIMESTAMP::TEXT, 'Date d''initialisation de la base'),
    ('environment', 'development', 'Environnement (development/production)')
ON CONFLICT (config_key) DO NOTHING;

-- Accorder les permissions sur la table system_config
GRANT ALL ON system_config TO sigeti_user;
GRANT ALL ON system_config_id_seq TO sigeti_user;

-- Afficher un résumé de l'initialisation
SELECT 
    'Base sigeti_dwh initialisée avec succès!' as status,
    current_database() as database,
    current_user as user,
    CURRENT_TIMESTAMP as initialized_at;

-- Lister les schémas créés
SELECT 
    'Schémas disponibles:' as info,
    string_agg(schema_name, ', ') as schemas
FROM information_schema.schemata 
WHERE schema_name IN ('public', 'staging', 'dwh', 'reporting');

-- Lister les extensions installées
SELECT 
    'Extensions installées:' as info,
    string_agg(extname, ', ') as extensions
FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'btree_gin', 'pg_trgm');