-- =====================================================================
-- CRÉATION DES DIMENSIONS POUR COLLECTES ET RECOUVREMENT
-- =====================================================================
-- Script pour créer les dimensions manquantes pour le module collectes
-- Suit le modèle dimensionnel existant avec clés surrogate
-- =====================================================================

-- =====================================================================
-- 1. DIMENSION AGENTS COLLECTEURS
-- =====================================================================
DROP TABLE IF EXISTS public.dim_agents_collecteurs CASCADE;

CREATE TABLE public.dim_agents_collecteurs (
    -- Clé surrogate
    agent_key TEXT PRIMARY KEY,
    
    -- Clé naturelle
    agent_id INTEGER NOT NULL,
    
    -- Attributs de l'agent
    nom_agent VARCHAR(200),
    prenom_agent VARCHAR(200),
    nom_complet VARCHAR(400),
    matricule VARCHAR(50),
    fonction VARCHAR(100),
    
    -- Informations de contact
    telephone VARCHAR(20),
    email VARCHAR(100),
    
    -- Statut et affectation
    statut_agent VARCHAR(20),
    zone_affectation_id INTEGER,
    
    -- Informations temporelles
    date_embauche DATE,
    
    -- Métadonnées SCD Type 2
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_debut_validite TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_fin_validite TIMESTAMP DEFAULT '9999-12-31 23:59:59',
    version_courante BOOLEAN DEFAULT TRUE,
    
    -- Index et contraintes
    UNIQUE(agent_id, date_debut_validite)
);

-- Index pour performance
CREATE INDEX idx_dim_agents_agent_id ON public.dim_agents_collecteurs(agent_id);
CREATE INDEX idx_dim_agents_statut ON public.dim_agents_collecteurs(statut_agent);
CREATE INDEX idx_dim_agents_version ON public.dim_agents_collecteurs(version_courante);

-- =====================================================================
-- 2. DIMENSION TYPES COLLECTES
-- =====================================================================
DROP TABLE IF EXISTS public.dim_types_collectes CASCADE;

CREATE TABLE public.dim_types_collectes (
    -- Clé surrogate
    type_collecte_key TEXT PRIMARY KEY,
    
    -- Attributs du type
    type_collecte VARCHAR(50) NOT NULL,
    libelle_court VARCHAR(100),
    libelle_long VARCHAR(200),
    description TEXT,
    
    -- Classification
    categorie VARCHAR(50), -- REDEVANCE, IMPOT, TAXE, AMENDE
    sous_categorie VARCHAR(50),
    
    -- Règles de gestion
    periodicite VARCHAR(20), -- MENSUELLE, TRIMESTRIELLE, ANNUELLE
    montant_base DECIMAL(15,2),
    taux_applicable DECIMAL(5,4),
    
    -- Statut
    actif BOOLEAN DEFAULT TRUE,
    
    -- Métadonnées
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contraintes
    UNIQUE(type_collecte)
);

-- Index
CREATE INDEX idx_dim_types_categorie ON public.dim_types_collectes(categorie);
CREATE INDEX idx_dim_types_actif ON public.dim_types_collectes(actif);

-- =====================================================================
-- 3. DIMENSION STATUTS COLLECTES
-- =====================================================================
DROP TABLE IF EXISTS public.dim_statuts_collectes CASCADE;

CREATE TABLE public.dim_statuts_collectes (
    -- Clé surrogate
    statut_collecte_key TEXT PRIMARY KEY,
    
    -- Attributs du statut
    statut_collecte VARCHAR(50) NOT NULL,
    libelle_statut VARCHAR(100),
    description TEXT,
    
    -- Classification
    categorie_statut VARCHAR(30), -- ACTIVE, INACTIVE, TERMINEE
    ordre_statut INTEGER, -- Pour ordonner les statuts
    
    -- Indicateurs
    est_recouvrable BOOLEAN DEFAULT TRUE,
    est_termine BOOLEAN DEFAULT FALSE,
    necessite_action BOOLEAN DEFAULT FALSE,
    
    -- Couleur pour affichage (optionnel)
    couleur_affichage VARCHAR(7), -- Code couleur hexadecimal
    
    -- Métadonnées
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contraintes
    UNIQUE(statut_collecte)
);

-- Index
CREATE INDEX idx_dim_statuts_categorie ON public.dim_statuts_collectes(categorie_statut);
CREATE INDEX idx_dim_statuts_ordre ON public.dim_statuts_collectes(ordre_statut);

-- =====================================================================
-- 4. DIMENSION MODES PAIEMENT
-- =====================================================================
DROP TABLE IF EXISTS public.dim_modes_paiement CASCADE;

CREATE TABLE public.dim_modes_paiement (
    -- Clé surrogate
    mode_paiement_key TEXT PRIMARY KEY,
    
    -- Attributs du mode
    mode_paiement VARCHAR(30) NOT NULL,
    libelle VARCHAR(100),
    description TEXT,
    
    -- Classification
    type_mode VARCHAR(20), -- ELECTRONIQUE, PHYSIQUE, BANCAIRE
    delai_encaissement_jours INTEGER,
    frais_percentage DECIMAL(5,4),
    
    -- Statut
    actif BOOLEAN DEFAULT TRUE,
    disponible_collecte BOOLEAN DEFAULT TRUE,
    
    -- Métadonnées
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contraintes
    UNIQUE(mode_paiement)
);

-- =====================================================================
-- 5. INITIALISATION DES DONNÉES DE RÉFÉRENCE
-- =====================================================================

-- Types de collectes
INSERT INTO public.dim_types_collectes (
    type_collecte_key, type_collecte, libelle_court, libelle_long, 
    categorie, periodicite, actif
) VALUES 
('TYP_RECOUVREMENT', 'RECOUVREMENT', 'Recouvrement', 'Recouvrement de créances', 'RECOUVREMENT', 'PONCTUELLE', true),
('TYP_REDEVANCE', 'REDEVANCE', 'Redevance', 'Redevance d''occupation', 'REDEVANCE', 'ANNUELLE', true),
('TYP_IMPOT', 'IMPOT', 'Impôt', 'Impôt sur les bénéfices', 'IMPOT', 'ANNUELLE', true),
('TYP_TAXE', 'TAXE', 'Taxe', 'Taxe professionnelle', 'TAXE', 'ANNUELLE', true),
('TYP_AMENDE', 'AMENDE', 'Amende', 'Amende pour retard', 'AMENDE', 'PONCTUELLE', true);

-- Statuts de collectes
INSERT INTO public.dim_statuts_collectes (
    statut_collecte_key, statut_collecte, libelle_statut, description,
    categorie_statut, ordre_statut, est_recouvrable, est_termine, necessite_action, couleur_affichage
) VALUES 
('STAT_EN_COURS', 'EN_COURS', 'En cours', 'Collecte en cours de traitement', 'ACTIVE', 1, true, false, true, '#FFA500'),
('STAT_RECOUVREE', 'RECOUVREE', 'Recouvrée', 'Collecte entièrement recouvrée', 'TERMINEE', 5, false, true, false, '#28A745'),
('STAT_PART_RECOUVREE', 'PARTIELLEMENT_RECOUVREE', 'Partiellement recouvrée', 'Collecte partiellement recouvrée', 'ACTIVE', 3, true, false, true, '#FFC107'),
('STAT_NON_RECOUVREE', 'NON_RECOUVREE', 'Non recouvrée', 'Collecte non recouvrée', 'ACTIVE', 2, true, false, true, '#DC3545'),
('STAT_ANNULEE', 'ANNULEE', 'Annulée', 'Collecte annulée', 'INACTIVE', 6, false, true, false, '#6C757D'),
('STAT_SUSPENDUE', 'SUSPENDUE', 'Suspendue', 'Collecte temporairement suspendue', 'INACTIVE', 4, false, false, true, '#17A2B8');

-- Modes de paiement
INSERT INTO public.dim_modes_paiement (
    mode_paiement_key, mode_paiement, libelle, description,
    type_mode, delai_encaissement_jours, frais_percentage, actif
) VALUES 
('MODE_ESPECE', 'ESPECE', 'Espèces', 'Paiement en espèces', 'PHYSIQUE', 0, 0.0000, true),
('MODE_CHEQUE', 'CHEQUE', 'Chèque', 'Paiement par chèque', 'BANCAIRE', 3, 0.0000, true),
('MODE_VIREMENT', 'VIREMENT', 'Virement', 'Virement bancaire', 'ELECTRONIQUE', 1, 0.0050, true),
('MODE_CB', 'CARTE_BANCAIRE', 'Carte bancaire', 'Paiement par carte bancaire', 'ELECTRONIQUE', 1, 0.0250, true),
('MODE_MOBILE', 'MOBILE_MONEY', 'Mobile Money', 'Paiement mobile', 'ELECTRONIQUE', 0, 0.0150, true);

-- =====================================================================
-- 6. COMMENTAIRES ET DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE public.dim_agents_collecteurs IS 'Dimension des agents collecteurs avec support SCD Type 2';
COMMENT ON COLUMN public.dim_agents_collecteurs.agent_key IS 'Clé surrogate unique pour l''agent';
COMMENT ON COLUMN public.dim_agents_collecteurs.version_courante IS 'Indique si c''est la version actuelle de l''agent';

COMMENT ON TABLE public.dim_types_collectes IS 'Dimension des types de collectes et leurs règles';
COMMENT ON TABLE public.dim_statuts_collectes IS 'Dimension des statuts de collectes avec workflow';
COMMENT ON TABLE public.dim_modes_paiement IS 'Dimension des modes de paiement et leurs caractéristiques';

-- =====================================================================
-- FIN DU SCRIPT
-- =====================================================================

COMMIT;

-- Vérification
SELECT 'Dimensions créées avec succès:' as resultat;
SELECT 'dim_agents_collecteurs: ' || COUNT(*) || ' structure créée' FROM information_schema.tables WHERE table_name = 'dim_agents_collecteurs';
SELECT 'dim_types_collectes: ' || COUNT(*) || ' enregistrements' FROM public.dim_types_collectes;
SELECT 'dim_statuts_collectes: ' || COUNT(*) || ' enregistrements' FROM public.dim_statuts_collectes;
SELECT 'dim_modes_paiement: ' || COUNT(*) || ' enregistrements' FROM public.dim_modes_paiement;