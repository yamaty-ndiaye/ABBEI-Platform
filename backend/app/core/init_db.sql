-- ============================================
-- ABBEI Platform - Database Schema
-- ============================================

-- ============================================
-- SCHEMA: activite
-- ============================================

CREATE TABLE activite.bailleurs (
    id SERIAL PRIMARY KEY,
    code_bailleur TEXT UNIQUE NOT NULL,  -- H76, LOGEAL...
    nom TEXT NOT NULL,
    adresse TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE activite.bons_commande (
    id SERIAL PRIMARY KEY,
    numero_bc TEXT UNIQUE NOT NULL,          -- 50654
    reference_interne TEXT,                  -- I61032025-50654
    bailleur_id INT NOT NULL,
    reference_marche TEXT,                   -- MA-2023-052A
    contact_abbei TEXT,
    statut TEXT DEFAULT 'en_cours'
        CHECK (statut IN ('en_cours', 'termine', 'annule', 'facture')),
    source_fichier TEXT,                     -- nom du fichier PDF source
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_bailleur
        FOREIGN KEY (bailleur_id)
        REFERENCES activite.bailleurs(id)
);

CREATE TABLE activite.bons_intervention (
    id SERIAL PRIMARY KEY,
    bon_commande_id INT NOT NULL,
    numero_intervention TEXT,
    adresse_chantier TEXT,
    description_travaux TEXT,
    metier TEXT CHECK (metier IN ('Peinture', 'Sol', 'Maconnerie', 'MultiService', 'SousTraitance')),
    date_debut DATE,
    date_fin DATE,
    statut TEXT DEFAULT 'en_cours'
        CHECK (statut IN ('en_cours', 'termine', 'annule')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_bon_commande
        FOREIGN KEY (bon_commande_id)
        REFERENCES activite.bons_commande(id)
        ON DELETE CASCADE
);

CREATE TABLE activite.prestations (
    id SERIAL PRIMARY KEY,
    bon_intervention_id INT NOT NULL,
    code_prestation TEXT,
    libelle TEXT,
    montant_ht NUMERIC(10,2),
    tva NUMERIC(5,2),
    montant_ttc NUMERIC(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_bon_intervention
        FOREIGN KEY (bon_intervention_id)
        REFERENCES activite.bons_intervention(id)
        ON DELETE CASCADE
);

-- ============================================
-- SCHEMA: facturation
-- ============================================

CREATE TABLE facturation.factures (
    id SERIAL PRIMARY KEY,
    numero_facture TEXT UNIQUE NOT NULL,     -- F150206_2025_35
    numero_facture_bailleur TEXT,            -- F250904554
    bon_commande_id INT,
    bailleur_id INT,
    type_facturation TEXT
        CHECK (type_facturation IN ('ENTRETIEN', 'SINISTRE', 'TRAVAUX')),
    montant_ht NUMERIC(10,2),
    montant_tva NUMERIC(10,2),
    montant_ttc NUMERIC(10,2),
    statut TEXT DEFAULT 'emise'
        CHECK (statut IN ('emise', 'payee', 'en_attente', 'annulee')),
    date_facture DATE,
    mois TEXT,
    annee INT,
    source_fichier TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_bon_commande_facture
        FOREIGN KEY (bon_commande_id)
        REFERENCES activite.bons_commande(id)
);

-- ============================================
-- SCHEMA: rh
-- ============================================

CREATE TABLE rh.salaries (
    id SERIAL PRIMARY KEY,
    reference TEXT UNIQUE NOT NULL,      -- référence interne ABBEI (34, 36...)
    civilite TEXT,
    nom TEXT NOT NULL,
    prenom TEXT,
    email TEXT,
    telephone TEXT,
    type_contrat TEXT
        CHECK (type_contrat IN ('CDI', 'CDDI', 'Interim')),
    site TEXT
        CHECK (site IN ('Saint-Etienne-du-Rouvray', 'Le Havre', 'Louviers')),
    date_entree DATE,
    date_sortie DATE,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- SCHEMA: raw
-- ============================================

CREATE TABLE raw.pdf_extractions (
    id SERIAL PRIMARY KEY,
    nom_fichier TEXT NOT NULL,
    chemin_fichier TEXT,
    type_document TEXT,      -- BC, BT, FACTURE, RH
    contenu_brut JSONB,      -- données extraites par l'agent IA
    statut TEXT DEFAULT 'a_traiter'
        CHECK (statut IN ('a_traiter', 'traite', 'erreur', 'ignore')),
    erreur TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);