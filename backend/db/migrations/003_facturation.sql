-- ============================================================
-- Migration 003 — Schéma facturation
-- Projet     : ABBEI Platform
-- Date       : 2026-06-23
-- Description: Factures émises par ABBEI aux bailleurs
-- ============================================================

CREATE TABLE facturation.factures (
    id SERIAL PRIMARY KEY,
    numero_facture TEXT NOT NULL UNIQUE,
    bailleur_id INTEGER REFERENCES activite.bailleurs(id),
    bon_commande_id INTEGER REFERENCES activite.bons_commande(id),
    date_facture DATE,
    montant_ht NUMERIC(10,2),
    montant_tva NUMERIC(10,2),
    montant_ttc NUMERIC(10,2),
    statut TEXT DEFAULT 'emise',
    fichier_pdf TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);