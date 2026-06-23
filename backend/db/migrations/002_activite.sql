-- ============================================================
-- Migration 002 — Schéma activite
-- Projet     : ABBEI Platform
-- Date       : 2026-06-23
-- Description: Tables métiers ABBEI (bailleurs, bons de 
--              commande, bons d'intervention, prestations)
-- ============================================================

-- Bailleurs (donneurs d'ordre)
CREATE TABLE activite.bailleurs (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    code TEXT UNIQUE,
    adresse TEXT,
    contact TEXT,
    email TEXT,
    telephone TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bons de commande
CREATE TABLE activite.bons_commande (
    id SERIAL PRIMARY KEY,
    numero_bc TEXT NOT NULL UNIQUE,
    bailleur_id INTEGER REFERENCES activite.bailleurs(id),
    date_emission DATE,
    date_reception DATE,
    montant_ht NUMERIC(10,2),
    statut TEXT DEFAULT 'recu',
    fichier_pdf TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bons d'intervention
CREATE TABLE activite.bons_intervention (
    id SERIAL PRIMARY KEY,
    numero_bi TEXT NOT NULL UNIQUE,
    bon_commande_id INTEGER REFERENCES activite.bons_commande(id),
    date_intervention DATE,
    adresse_chantier TEXT,
    statut TEXT DEFAULT 'planifie',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Prestations réalisées
CREATE TABLE activite.prestations (
    id SERIAL PRIMARY KEY,
    bon_intervention_id INTEGER REFERENCES activite.bons_intervention(id),
    designation TEXT NOT NULL,
    quantite NUMERIC(10,2),
    unite TEXT,
    prix_unitaire NUMERIC(10,2),
    montant_ht NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);