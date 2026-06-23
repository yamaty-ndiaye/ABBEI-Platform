# ============================================================
# Tests unitaires — detecter_anomalies
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Vérifie la logique de détection des anomalies
#              sans base de données ni API externe
# ============================================================

import pytest
from app.agents.invoice_agent import detecter_anomalies

# ── Tarif de référence pour les tests ───────────────────────
TARIF_TEST = {
    "REF001": {"designation": "PEINTURE BLANC 15L",  "prix": 75.00},
    "REF002": {"designation": "MANCHON 180MM",        "prix": 5.00},
    "REF003": {"designation": "ENDUIT REBOUCHEUR 5KG","prix": 13.40},
}


# ── Tests ECART_PRIX ─────────────────────────────────────────
def test_ecart_prix_detecte():
    """Un article facturé plus cher que le tarif → ECART_PRIX."""
    lignes = [{
        "reference": "REF001",
        "designation": "PEINTURE BLANC 15L",
        "quantite": 2,
        "prix_unitaire": 90.00,  # tarif = 75.00 → écart
        "montant_ht": 180.00
    }]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)

    assert len(anomalies) == 1
    assert anomalies[0]["type_anomalie"] == "ECART_PRIX"
    assert anomalies[0]["prix_tarif"] == 75.00
    assert anomalies[0]["ecart_ht"] == 30.00  # (90-75) * 2


def test_pas_anomalie_si_prix_inferieur():
    """Un article facturé moins cher que le tarif → pas d'anomalie."""
    lignes = [{
        "reference": "REF002",
        "designation": "MANCHON 180MM",
        "quantite": 10,
        "prix_unitaire": 4.50,  # tarif = 5.00 → favorable
        "montant_ht": 45.00
    }]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)
    assert len(anomalies) == 0


def test_pas_anomalie_si_prix_egal():
    """Un article facturé au prix exact du tarif → pas d'anomalie."""
    lignes = [{
        "reference": "REF002",
        "designation": "MANCHON 180MM",
        "quantite": 5,
        "prix_unitaire": 5.00,  # prix exact
        "montant_ht": 25.00
    }]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)
    assert len(anomalies) == 0


# ── Tests HORS_BORDEREAU ─────────────────────────────────────
def test_hors_bordereau_detecte():
    """Une référence absente du tarif → HORS_BORDEREAU."""
    lignes = [{
        "reference": "REF999",
        "designation": "PRODUIT INCONNU",
        "quantite": 3,
        "prix_unitaire": 20.00,
        "montant_ht": 60.00
    }]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)

    assert len(anomalies) == 1
    assert anomalies[0]["type_anomalie"] == "HORS_BORDEREAU"
    assert anomalies[0]["prix_tarif"] is None
    assert anomalies[0]["ecart_ht"] == 60.00  # 20 * 3


def test_sans_reference_ignore():
    """Une ligne sans référence est ignorée."""
    lignes = [{
        "reference": None,
        "designation": "ECO PARTICIPATION",
        "quantite": 1,
        "prix_unitaire": 2.50,
        "montant_ht": 2.50
    }]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)
    assert len(anomalies) == 0


# ── Tests cas mixtes ─────────────────────────────────────────
def test_plusieurs_lignes_mixtes():
    """
    3 lignes : 1 conforme, 1 écart prix, 1 hors bordereau
    → 2 anomalies détectées.
    """
    lignes = [
        {
            "reference": "REF001",
            "designation": "PEINTURE BLANC 15L",
            "quantite": 1,
            "prix_unitaire": 75.00,  # conforme
            "montant_ht": 75.00
        },
        {
            "reference": "REF003",
            "designation": "ENDUIT REBOUCHEUR 5KG",
            "quantite": 4,
            "prix_unitaire": 18.00,  # écart : tarif = 13.40
            "montant_ht": 72.00
        },
        {
            "reference": "REF999",
            "designation": "PRODUIT ABSENT",
            "quantite": 2,
            "prix_unitaire": 30.00,  # hors bordereau
            "montant_ht": 60.00
        }
    ]
    anomalies = detecter_anomalies(lignes, TARIF_TEST)

    assert len(anomalies) == 2

    types = [a["type_anomalie"] for a in anomalies]
    assert "ECART_PRIX" in types
    assert "HORS_BORDEREAU" in types


def test_tarif_vide():
    """Tarif vide → toutes les lignes avec référence sont HORS_BORDEREAU."""
    lignes = [
        {"reference": "REF001", "designation": "PEINTURE", "quantite": 1, "prix_unitaire": 75.00, "montant_ht": 75.00},
        {"reference": "REF002", "designation": "MANCHON",  "quantite": 2, "prix_unitaire": 5.00,  "montant_ht": 10.00},
    ]
    anomalies = detecter_anomalies(lignes, {})

    assert len(anomalies) == 2
    assert all(a["type_anomalie"] == "HORS_BORDEREAU" for a in anomalies)


def test_lignes_vides():
    """Aucune ligne → aucune anomalie."""
    anomalies = detecter_anomalies([], TARIF_TEST)
    assert len(anomalies) == 0