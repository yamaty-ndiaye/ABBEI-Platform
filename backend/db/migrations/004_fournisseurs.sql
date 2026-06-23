-- ============================================================
-- Migration 004 — Schéma fournisseurs
-- Projet     : ABBEI Platform
-- Date       : 2026-06-23
-- Description: Factures fournisseurs, tarifs et anomalies
--              (agent IA de contrôle tarifaire)
-- ============================================================

-- Tarifs par fournisseur (chargés depuis Excel chaque année)
CREATE TABLE fournisseurs.tarifs (
    id SERIAL PRIMARY KEY,
    fournisseur TEXT NOT NULL,
    annee INTEGER NOT NULL,
    reference TEXT NOT NULL,
    designation TEXT NOT NULL,
    prix_unitaire NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(fournisseur, annee, reference)
);

-- Factures reçues des fournisseurs
CREATE TABLE fournisseurs.factures (
    id SERIAL PRIMARY KEY,
    numero_facture TEXT NOT NULL,
    fournisseur TEXT NOT NULL,
    client TEXT,
    date_facture DATE,
    montant_ht NUMERIC(10,2),
    fichier_pdf TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Lignes détaillées de chaque facture
CREATE TABLE fournisseurs.lignes_facture (
    id SERIAL PRIMARY KEY,
    facture_id INTEGER REFERENCES fournisseurs.factures(id) ON DELETE CASCADE,
    reference TEXT,
    designation TEXT NOT NULL,
    quantite NUMERIC(10,2),
    prix_unitaire NUMERIC(10,2),
    montant_ht NUMERIC(10,2)
);

-- Anomalies détectées par l'agent
CREATE TABLE fournisseurs.anomalies (
    id SERIAL PRIMARY KEY,
    facture_id INTEGER REFERENCES fournisseurs.factures(id) ON DELETE CASCADE,
    ligne_id INTEGER REFERENCES fournisseurs.lignes_facture(id) ON DELETE CASCADE,
    reference TEXT,
    designation TEXT,
    type_anomalie TEXT NOT NULL,
    prix_facture NUMERIC(10,2),
    prix_tarif NUMERIC(10,2),
    ecart_ht NUMERIC(10,2),
    commentaire TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);