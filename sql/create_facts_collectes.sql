-- =====================================================================
-- CRÉATION DES TABLES DE FAITS POUR COLLECTES ET RECOUVREMENT
-- =====================================================================
-- Script pour créer les tables de faits du module collectes
-- Suivent le modèle en étoile avec clés étrangères vers les dimensions
-- =====================================================================

-- =====================================================================
-- 1. TABLE DE FAIT COLLECTES
-- =====================================================================
DROP TABLE IF EXISTS public.fct_collectes CASCADE;

CREATE TABLE public.fct_collectes (
    -- Clé primaire surrogate
    collecte_fact_key BIGSERIAL PRIMARY KEY,
    
    -- Clé naturelle
    collecte_id INTEGER NOT NULL,
    
    -- Clés étrangères vers les dimensions (modèle en étoile)
    date_creation_key INTEGER,           -- Vers dim_date
    date_echeance_key INTEGER,           -- Vers dim_date  
    date_recouvrement_key INTEGER,       -- Vers dim_date (peut être NULL)
    date_modification_key INTEGER,       -- Vers dim_date
    
    agent_collecteur_key TEXT,           -- Vers dim_agents_collecteurs
    type_collecte_key TEXT,              -- Vers dim_types_collectes
    statut_collecte_key TEXT,            -- Vers dim_statuts_collectes
    entreprise_key TEXT,                 -- Vers dim_entreprises (existante)
    lot_key TEXT,                        -- Vers dim_lots (existante)
    zone_key TEXT,                       -- Vers dim_zones_industrielles (existante)
    
    -- Faits (mesures)
    montant_a_collecter DECIMAL(15,2),
    montant_collecte DECIMAL(15,2),
    montant_restant_du DECIMAL(15,2),
    
    -- Faits dérivés (calculés)
    taux_recouvrement DECIMAL(5,4),
    delai_recouvrement_jours INTEGER,
    est_en_retard BOOLEAN,
    nombre_jours_retard INTEGER,
    
    -- Métadonnées
    reference VARCHAR(50),
    observations TEXT,
    demande_attribution_id INTEGER,
    
    -- Audit
    date_chargement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id TEXT,
    
    -- Contraintes
    UNIQUE(collecte_id),
    CHECK (montant_a_collecter >= 0),
    CHECK (montant_collecte >= 0),
    CHECK (taux_recouvrement >= 0 AND taux_recouvrement <= 1)
);

-- Index pour performance
CREATE INDEX idx_fct_collectes_date_creation ON public.fct_collectes(date_creation_key);
CREATE INDEX idx_fct_collectes_agent ON public.fct_collectes(agent_collecteur_key);
CREATE INDEX idx_fct_collectes_type ON public.fct_collectes(type_collecte_key);
CREATE INDEX idx_fct_collectes_statut ON public.fct_collectes(statut_collecte_key);
CREATE INDEX idx_fct_collectes_entreprise ON public.fct_collectes(entreprise_key);
CREATE INDEX idx_fct_collectes_montant ON public.fct_collectes(montant_a_collecter);
CREATE INDEX idx_fct_collectes_retard ON public.fct_collectes(est_en_retard);

-- =====================================================================
-- 2. TABLE DE FAIT RECOUVREMENTS
-- =====================================================================
DROP TABLE IF EXISTS public.fct_recouvrements CASCADE;

CREATE TABLE public.fct_recouvrements (
    -- Clé primaire surrogate  
    recouvrement_fact_key BIGSERIAL PRIMARY KEY,
    
    -- Clé naturelle
    recouvrement_id INTEGER NOT NULL,
    
    -- Relation avec la collecte parente
    collecte_fact_key BIGINT,            -- FK vers fct_collectes
    collecte_id INTEGER,                 -- Clé naturelle pour jointures
    
    -- Clés étrangères vers les dimensions
    date_action_key INTEGER,             -- Vers dim_date
    date_creation_key INTEGER,           -- Vers dim_date
    date_modification_key INTEGER,       -- Vers dim_date
    
    agent_recouvrement_key TEXT,         -- Vers dim_agents_collecteurs
    type_action_key TEXT,                -- Vers nouvelle dim_types_actions (à créer si nécessaire)
    statut_recouvrement_key TEXT,        -- Vers nouvelle dim_statuts_recouvrements
    
    -- Faits (mesures)
    montant_paiement DECIMAL(15,2),
    frais_recouvrement DECIMAL(15,2) DEFAULT 0,
    montant_net DECIMAL(15,2),
    
    -- Faits dérivés
    efficacite_action DECIMAL(5,4),      -- % du montant récupéré vs montant dû
    delai_depuis_creation_collecte INTEGER,
    
    -- Métadonnées
    type_action VARCHAR(50),
    mode_paiement VARCHAR(20),
    statut_recouvrement VARCHAR(20),
    observations TEXT,
    piece_justificative TEXT,
    
    -- Audit  
    date_chargement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_batch_id TEXT,
    
    -- Contraintes
    UNIQUE(recouvrement_id),
    CHECK (montant_paiement >= 0),
    CHECK (frais_recouvrement >= 0)
);

-- Index pour performance
CREATE INDEX idx_fct_recouvrements_collecte ON public.fct_recouvrements(collecte_id);
CREATE INDEX idx_fct_recouvrements_date_action ON public.fct_recouvrements(date_action_key);
CREATE INDEX idx_fct_recouvrements_agent ON public.fct_recouvrements(agent_recouvrement_key);
CREATE INDEX idx_fct_recouvrements_montant ON public.fct_recouvrements(montant_paiement);
CREATE INDEX idx_fct_recouvrements_type_action ON public.fct_recouvrements(type_action);

-- =====================================================================
-- 3. CLÉS ÉTRANGÈRES (CONTRAINTES RÉFÉRENTIELLES)
-- =====================================================================

-- fct_collectes vers dimensions
ALTER TABLE public.fct_collectes 
ADD CONSTRAINT fk_collectes_agent_collecteur 
FOREIGN KEY (agent_collecteur_key) REFERENCES public.dim_agents_collecteurs(agent_key);

ALTER TABLE public.fct_collectes 
ADD CONSTRAINT fk_collectes_type_collecte 
FOREIGN KEY (type_collecte_key) REFERENCES public.dim_types_collectes(type_collecte_key);

ALTER TABLE public.fct_collectes 
ADD CONSTRAINT fk_collectes_statut_collecte 
FOREIGN KEY (statut_collecte_key) REFERENCES public.dim_statuts_collectes(statut_collecte_key);

-- fct_recouvrements vers dimensions et fct_collectes
ALTER TABLE public.fct_recouvrements 
ADD CONSTRAINT fk_recouvrements_collecte_fact 
FOREIGN KEY (collecte_fact_key) REFERENCES public.fct_collectes(collecte_fact_key);

ALTER TABLE public.fct_recouvrements 
ADD CONSTRAINT fk_recouvrements_agent 
FOREIGN KEY (agent_recouvrement_key) REFERENCES public.dim_agents_collecteurs(agent_key);

-- =====================================================================
-- 4. VUES MATÉRIALISÉES POUR PERFORMANCE (OPTIONNEL)
-- =====================================================================

-- Vue pré-agrégée pour les KPI
DROP MATERIALIZED VIEW IF EXISTS public.mv_kpi_collectes_summary CASCADE;

CREATE MATERIALIZED VIEW public.mv_kpi_collectes_summary AS
SELECT 
    -- Dimensions de groupement
    dc.date_complete as date_collecte,
    a.nom_complet as agent_collecteur,
    tc.categorie as categorie_collecte,
    sc.libelle_statut as statut,
    
    -- Agrégats
    COUNT(*) as nombre_collectes,
    SUM(fc.montant_a_collecter) as montant_total_du,
    SUM(fc.montant_collecte) as montant_total_collecte,
    SUM(fc.montant_restant_du) as montant_restant_du,
    AVG(fc.taux_recouvrement) as taux_recouvrement_moyen,
    AVG(fc.delai_recouvrement_jours) as delai_moyen_jours,
    
    -- Compteurs
    COUNT(CASE WHEN fc.est_en_retard THEN 1 END) as nombre_en_retard,
    COUNT(CASE WHEN sc.est_termine THEN 1 END) as nombre_terminees,
    
    -- Métadonnées
    CURRENT_TIMESTAMP as derniere_maj
    
FROM public.fct_collectes fc
LEFT JOIN public.dim_date dc ON fc.date_creation_key = dc.date_key
LEFT JOIN public.dim_agents_collecteurs a ON fc.agent_collecteur_key = a.agent_key
LEFT JOIN public.dim_types_collectes tc ON fc.type_collecte_key = tc.type_collecte_key  
LEFT JOIN public.dim_statuts_collectes sc ON fc.statut_collecte_key = sc.statut_collecte_key

GROUP BY 
    dc.date_complete,
    a.nom_complet,
    tc.categorie,
    sc.libelle_statut;

-- Index sur la vue matérialisée
CREATE INDEX idx_mv_kpi_collectes_date ON public.mv_kpi_collectes_summary(date_collecte);
CREATE INDEX idx_mv_kpi_collectes_agent ON public.mv_kpi_collectes_summary(agent_collecteur);

-- =====================================================================
-- 5. COMMENTAIRES ET DOCUMENTATION
-- =====================================================================

COMMENT ON TABLE public.fct_collectes IS 'Table de fait des collectes - Modèle en étoile';
COMMENT ON COLUMN public.fct_collectes.collecte_fact_key IS 'Clé surrogate unique pour le fait collecte';
COMMENT ON COLUMN public.fct_collectes.taux_recouvrement IS 'Taux de recouvrement (0-1)';
COMMENT ON COLUMN public.fct_collectes.delai_recouvrement_jours IS 'Nombre de jours entre création et recouvrement complet';

COMMENT ON TABLE public.fct_recouvrements IS 'Table de fait des actions de recouvrement';
COMMENT ON COLUMN public.fct_recouvrements.efficacite_action IS 'Efficacité de l''action (montant récupéré / montant dû)';

COMMENT ON MATERIALIZED VIEW public.mv_kpi_collectes_summary IS 'Vue matérialisée pré-agrégée pour les KPI collectes';

-- =====================================================================
-- FIN DU SCRIPT
-- =====================================================================

-- Vérification
SELECT 'Tables de faits créées:' as resultat;
SELECT 'fct_collectes: structure créée' as info;
SELECT 'fct_recouvrements: structure créée' as info;
SELECT 'mv_kpi_collectes_summary: vue matérialisée créée' as info;