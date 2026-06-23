# ============================================================
# Tests unitaires — charger_tarif
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Vérifie la lecture du fichier Excel tarif
#              sans base de données (mock de SessionLocal)
# ============================================================

import pytest
import openpyxl
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.agents.invoice_agent import charger_tarif


def creer_excel_test(lignes: list) -> bytes:
    """
    Utilitaire : crée un fichier Excel en mémoire pour les tests.
    lignes = [(reference, designation, prix), ...]
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    # En-têtes
    ws.append(["Article", "Libellé", "P.U"])
    # Données
    for ligne in lignes:
        ws.append(ligne)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ── Mock de la base de données ───────────────────────────────
# On ne veut pas toucher à PostgreSQL dans les tests unitaires
@pytest.fixture
def mock_db():
    """Remplace SessionLocal par un faux objet pour les tests."""
    with patch("app.agents.invoice_agent.SessionLocal") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


# ── Tests ────────────────────────────────────────────────────
def test_charger_tarif_basique(mock_db):
    """Tarif simple avec 3 articles → dict correctement construit."""
    excel = creer_excel_test([
        ("REF001", "PEINTURE BLANC 15L",   75.00),
        ("REF002", "MANCHON 180MM",         5.00),
        ("REF003", "ENDUIT REBOUCHEUR 5KG", 13.40),
    ])

    tarif = charger_tarif(excel, "OSCA", 2026)

    assert len(tarif) == 3
    assert "REF001" in tarif
    assert tarif["REF001"]["prix"] == 75.00
    assert tarif["REF001"]["designation"] == "PEINTURE BLANC 15L"


def test_charger_tarif_prix_float(mock_db):
    """Les prix sont bien convertis en float."""
    excel = creer_excel_test([
        ("REF001", "PRODUIT TEST", "12.05"),  # prix en string
    ])
    tarif = charger_tarif(excel, "OSCA", 2026)

    assert isinstance(tarif["REF001"]["prix"], float)
    assert tarif["REF001"]["prix"] == 12.05


def test_charger_tarif_ignore_lignes_vides(mock_db):
    """Les lignes sans référence ou sans prix sont ignorées."""
    excel = creer_excel_test([
        ("REF001", "PRODUIT VALIDE", 10.00),
        (None,     "SANS REFERENCE", 5.00),   # ignorée
        ("REF003", None,             8.00),   # ignorée
    ])
    tarif = charger_tarif(excel, "OSCA", 2026)

    assert len(tarif) == 1
    assert "REF001" in tarif


def test_charger_tarif_sauvegarde_en_base(mock_db):
    """Vérifie que la sauvegarde en base est bien appelée."""
    excel = creer_excel_test([
        ("REF001", "PEINTURE BLANC 15L", 75.00),
        ("REF002", "MANCHON 180MM",       5.00),
    ])

    charger_tarif(excel, "OSCA", 2026)

    # La session doit avoir été commitée
    mock_db.commit.assert_called_once()


def test_charger_tarif_vide(mock_db):
    """Fichier Excel sans données → tarif vide."""
    excel = creer_excel_test([])  # juste les en-têtes
    tarif = charger_tarif(excel, "OSCA", 2026)

    assert tarif == {}