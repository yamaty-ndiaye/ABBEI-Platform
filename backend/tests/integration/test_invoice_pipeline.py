# ============================================================
# Tests d'intégration — Pipeline factures
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Teste le pipeline complet avec la vraie base
#              PostgreSQL (schéma de test isolé)
# ============================================================

import pytest
import openpyxl
from io import BytesIO
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from app.core.database import SessionLocal
from app.agents.invoice_agent import (
    charger_tarif,
    detecter_anomalies,
    sauvegarder_facture,
    traiter_facture
)


# ── Fixtures ─────────────────────────────────────────────────
def creer_excel_test(lignes: list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Article", "Libellé", "P.U"])
    for ligne in lignes:
        ws.append(ligne)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def nettoyer_base():
    """
    Nettoie les données de test avant et après chaque test.
    autouse=True → s'exécute automatiquement pour chaque test.
    """
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM fournisseurs.anomalies"))
        db.execute(text("DELETE FROM fournisseurs.lignes_facture"))
        db.execute(text("DELETE FROM fournisseurs.factures WHERE fournisseur LIKE 'TEST_%'"))
        db.execute(text("DELETE FROM fournisseurs.tarifs WHERE fournisseur LIKE 'TEST_%'"))
        db.commit()
    finally:
        db.close()

    yield  # le test s'exécute ici

    # Nettoyage après le test
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM fournisseurs.anomalies"))
        db.execute(text("DELETE FROM fournisseurs.lignes_facture"))
        db.execute(text("DELETE FROM fournisseurs.factures WHERE fournisseur LIKE 'TEST_%'"))
        db.execute(text("DELETE FROM fournisseurs.tarifs WHERE fournisseur LIKE 'TEST_%'"))
        db.commit()
    finally:
        db.close()


# ── Tests ────────────────────────────────────────────────────
def test_charger_tarif_en_base():
    """Le tarif est bien inséré en PostgreSQL."""
    excel = creer_excel_test([
        ("REF001", "PEINTURE BLANC 15L", 75.00),
        ("REF002", "MANCHON 180MM",       5.00),
    ])

    tarif = charger_tarif(excel, "TEST_OSCA", 2026)

    # Vérification en base
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM fournisseurs.tarifs
            WHERE fournisseur = 'TEST_OSCA' AND annee = 2026
        """)).fetchone()
        assert result[0] == 2
    finally:
        db.close()


def test_sauvegarder_facture_en_base():
    """Une facture avec ses lignes et anomalies est bien insérée."""
    data = {
        "numero_facture": "TEST-FA001",
        "fournisseur":    "TEST_OSCA",
        "client":         "ABBEI",
        "date_facture":   "2026-06-23",
        "montant_ht":     180.00,
        "lignes": [
            {
                "reference":    "REF001",
                "designation":  "PEINTURE BLANC 15L",
                "quantite":     2,
                "prix_unitaire": 90.00,
                "montant_ht":   180.00
            }
        ]
    }
    anomalies = [{
        "reference":    "REF001",
        "designation":  "PEINTURE BLANC 15L",
        "type_anomalie": "ECART_PRIX",
        "prix_facture": 90.00,
        "prix_tarif":   75.00,
        "ecart_ht":     30.00,
        "commentaire":  "Facturé 90€ vs tarif 75€"
    }]

    facture_id = sauvegarder_facture(data, anomalies, "test_facture.pdf")

    # Vérifications en base
    db = SessionLocal()
    try:
        # Facture insérée
        facture = db.execute(text("""
            SELECT numero_facture, montant_ht
            FROM fournisseurs.factures WHERE id = :id
        """), {"id": facture_id}).fetchone()
        assert facture[0] == "TEST-FA001"
        assert float(facture[1]) == 180.00

        # Ligne insérée
        nb_lignes = db.execute(text("""
            SELECT COUNT(*) FROM fournisseurs.lignes_facture
            WHERE facture_id = :id
        """), {"id": facture_id}).fetchone()[0]
        assert nb_lignes == 1

        # Anomalie insérée
        nb_anomalies = db.execute(text("""
            SELECT COUNT(*) FROM fournisseurs.anomalies
            WHERE facture_id = :id
        """), {"id": facture_id}).fetchone()[0]
        assert nb_anomalies == 1

    finally:
        db.close()


def test_pipeline_complet_avec_mock_llm():
    """
    Test de non-régression : pipeline complet avec LLM mocké.
    Vérifie que toutes les étapes s'enchaînent correctement.
    """
    tarif = {
        "REF001": {"designation": "PEINTURE BLANC 15L",   "prix": 75.00},
        "REF002": {"designation": "MANCHON 180MM",         "prix": 5.00},
    }

    # On mock le LLM pour ne pas consommer de crédits API
    llm_response = {
        "numero_facture": "TEST-FA002",
        "fournisseur":    "TEST_OSCA",
        "client":         "ABBEI",
        "date_facture":   "2026-06-23",
        "montant_ht":     265.00,
        "lignes": [
            {
                "reference":    "REF001",
                "designation":  "PEINTURE BLANC 15L",
                "quantite":     2,
                "prix_unitaire": 90.00,  # écart : tarif = 75
                "montant_ht":   180.00
            },
            {
                "reference":    "REF999",
                "designation":  "PRODUIT HORS BORDEREAU",
                "quantite":     1,
                "prix_unitaire": 85.00,
                "montant_ht":   85.00
            }
        ]
    }

    # Création d'un PDF factice
    pdf_factice = b"%PDF-1.4 contenu test"

    with patch("app.agents.invoice_agent.extraire_texte_pdf", return_value="texte facture test"), \
         patch("app.agents.invoice_agent.analyser_facture_llm", return_value=llm_response):

        resultat = traiter_facture(pdf_factice, tarif, "test_pipeline.pdf")

    # Vérifications du résultat
    assert resultat["numero_facture"] == "TEST-FA002"
    assert resultat["nb_lignes"] == 2
    assert resultat["nb_anomalies"] == 2

    types = [a["type_anomalie"] for a in resultat["anomalies"]]
    assert "ECART_PRIX" in types
    assert "HORS_BORDEREAU" in types

    # Vérification en base
    db = SessionLocal()
    try:
        nb = db.execute(text("""
            SELECT COUNT(*) FROM fournisseurs.factures
            WHERE numero_facture = 'TEST-FA002'
        """)).fetchone()[0]
        assert nb == 1
    finally:
        db.close()