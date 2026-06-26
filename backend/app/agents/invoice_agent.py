# ============================================================
# Agent — Contrôle factures fournisseurs
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Extraction PDF + comparaison tarif par LLM
#              + insertion PostgreSQL
# ============================================================

import json
import base64
import openpyxl
from io import BytesIO
from anthropic import Anthropic
from sqlalchemy import text
from app.core.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.core.database import SessionLocal

client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ── 1. Lecture du tarif Excel ────────────────────────────────
def charger_tarif(fichier_excel: bytes, fournisseur: str, annee: int) -> dict:
    """
    Lit un fichier Excel tarif.
    Détecte automatiquement la ligne d'en-tête et les colonnes.
    Retourne un dict ET sauvegarde en PostgreSQL.
    """
    wb = openpyxl.load_workbook(BytesIO(fichier_excel), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    # Détection automatique de la ligne d'en-tête
    header_row_idx = 0
    for i, row in enumerate(rows):
        row_str = [str(v).lower() if v else "" for v in row]
        has_ref  = any("ref" in v or "article" in v or "code" in v for v in row_str)
        has_prix = any("prix" in v or "p.u" in v or "tarif" in v for v in row_str)
        if has_ref and has_prix:
            header_row_idx = i
            break

    headers  = [str(h).strip().lower() if h else "" for h in rows[header_row_idx]]
    col_ref  = next((i for i, h in enumerate(headers)
                     if "ref" in h or "article" in h or "code" in h), 0)
    col_des  = next((i for i, h in enumerate(headers)
                     if "lib" in h or "desig" in h or "nom" in h or "designation" in h), 1)
    col_prix = next((i for i, h in enumerate(headers)
                     if "prix" in h or "p.u" in h or "tarif" in h), 2)

    tarif = {}
    for row in rows[header_row_idx + 1:]:
        ref  = str(row[col_ref]).strip() if row[col_ref] else None
        des  = str(row[col_des]).strip() if row[col_des] else None
        prix = row[col_prix]

        if des and prix and des != "None":
            try:
                cle = ref if ref and ref != "None" else des
                tarif[cle] = {"designation": des, "prix": float(prix), "reference": ref}
            except (ValueError, TypeError):
                continue

    # Sauvegarde en base
    db = SessionLocal()
    try:
        for cle, data in tarif.items():
            db.execute(text("""
                INSERT INTO fournisseurs.tarifs
                    (fournisseur, annee, reference, designation, prix_unitaire)
                VALUES (:fournisseur, :annee, :ref, :des, :prix)
                ON CONFLICT (fournisseur, annee, reference) DO UPDATE
                SET designation   = EXCLUDED.designation,
                    prix_unitaire = EXCLUDED.prix_unitaire
            """), {
                "fournisseur": fournisseur, "annee": annee,
                "ref": cle, "des": data["designation"], "prix": data["prix"]
            })
        db.commit()
    finally:
        db.close()

    return tarif


# ── 2. Analyse LLM — PDF + tarif → anomalies directes ───────
def analyser_facture_llm(pdf_bytes: bytes, tarif: dict) -> dict:
    """
    Envoie le PDF ET le tarif complet à Claude.
    Claude fait lui-même la correspondance produit et détecte les anomalies.
    """
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    tarif_str = "\n".join([
        f"- {v.get('reference') or cle} | {v['designation']} | {v['prix']} €"
        for cle, v in tarif.items()
    ])

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=6000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64
                    }
                },
                {
                    "type": "text",
                    "text": f"""Tu es un expert comptable spécialisé dans le contrôle de facturation BTP.
Analyse cette facture fournisseur et compare chaque article au bordereau de prix ci-dessous.

BORDEREAU DE PRIX NÉGOCIÉ ABBEI :
{tarif_str}

Réponds UNIQUEMENT en JSON valide sans markdown :
{{
  "numero_facture": "numéro",
  "fournisseur": "nom du fournisseur",
  "client": "nom du client",
  "date_facture": "YYYY-MM-DD ou null",
  "montant_ht": 0.00,
  "nb_articles": 0,
  "type_document": "facture ou avoir ou rfa",
  "anomalies": [
    {{
      "reference": "référence article sur la facture",
      "designation": "désignation exacte sur la facture",
      "chantier": "chantier/référence BL si indiqué ou null",
      "quantite": 0.00,
      "unite": "U, M2, ML, L, KG ou null",
      "prix_catalogue": 0.00,
      "remise_pct": 0.00,
      "prix_unitaire": 0.00,
      "montant_ht": 0.00,
      "type_anomalie": "HORS_BORDEREAU ou ECART_PRIX",
      "prix_tarif": 0.00,
      "ecart_unitaire": 0.00,
      "ecart_pct": 0.00,
      "ecart_ht": 0.00,
      "cause_anomalie": "explication en une phrase"
    }}
  ]
}}

RÈGLES IMPORTANTES :
- Ignore les lignes éco-participation et surcoût énergétique
- Compare INTELLIGEMMENT : si la désignation est similaire même avec référence différente, c'est le même produit
- Ex: "FREITACCROCH BLANC 3L" = "FREITACCROCH nouvelle formule BLANC/GRIS 3L" → même produit
- Une anomalie ECART_PRIX = prix facturé STRICTEMENT SUPÉRIEUR au prix du bordereau
- Une anomalie HORS_BORDEREAU = produit vraiment absent du bordereau (pas de correspondance possible)
- Si prix facturé ≤ prix bordereau → pas d'anomalie, ne pas inclure dans la liste
- nb_articles = nombre total d'articles analysés hors éco-participation
- ecart_unitaire = prix_unitaire - prix_tarif
- ecart_pct = (ecart_unitaire / prix_tarif) * 100
- ecart_ht = ecart_unitaire * quantite
- cause_anomalie : explique pourquoi c'est une anomalie (version teintée, remise non appliquée, référence interne différente, produit hors gamme négociée...)
- "numero_facture" = numéro de facture (ex: 2603054673, FA409XXX) — PAS le numéro client (code commençant par 000...)
- "client" = nom du client destinataire (ABBEI, ST ETIENNE DU ROUVRAY...) — PAS le code client numérique
- Si l'écart de prix concerne une version teintée (mention couleur, CH2, RAL, teinte, BASE SEP, BASE IN...) → type_anomalie = "HORS_BORDEREAU" car c'est un produit différent du standard, pas un écart de prix à réclamer
- ECART_PRIX uniquement si c'est le même produit standard (blanc, incolore, standard) facturé à un prix supérieur au bordereau sans justification de couleur ou variante
- Si type_document est avoir ou rfa → anomalies = []"""
                }
            ]
        }]
    )

    # Extraction robuste du JSON
    texte = response.content[0].text.strip()
    debut = texte.find("{")
    fin   = texte.rfind("}") + 1
    texte = texte[debut:fin]
    return json.loads(texte)


# ── 3. Sauvegarde PostgreSQL ─────────────────────────────────
def sauvegarder_facture(data: dict, nom_fichier: str) -> int:
    """Insère la facture et ses anomalies en base."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            INSERT INTO fournisseurs.factures
                (numero_facture, fournisseur, client, date_facture, montant_ht, fichier_pdf)
            VALUES (:num, :fourn, :client, :date, :ht, :pdf)
            RETURNING id
        """), {
            "num":    data.get("numero_facture"),
            "fourn":  data.get("fournisseur"),
            "client": data.get("client"),
            "date":   data.get("date_facture"),
            "ht":     data.get("montant_ht"),
            "pdf":    nom_fichier
        })
        facture_id = result.fetchone()[0]

        for a in data.get("anomalies", []):
            res_ligne = db.execute(text("""
                INSERT INTO fournisseurs.lignes_facture
                    (facture_id, reference, designation, quantite, prix_unitaire, montant_ht)
                VALUES (:fid, :ref, :des, :qte, :pu, :ht)
                RETURNING id
            """), {
                "fid": facture_id,
                "ref": a.get("reference"),
                "des": a.get("designation"),
                "qte": a.get("quantite"),
                "pu":  a.get("prix_unitaire"),
                "ht":  a.get("montant_ht")
            })
            ligne_id = res_ligne.fetchone()[0]

            db.execute(text("""
                INSERT INTO fournisseurs.anomalies
                    (facture_id, ligne_id, reference, designation, type_anomalie,
                     prix_facture, prix_tarif, ecart_ht, commentaire)
                VALUES (:fid, :lid, :ref, :des, :type, :pf, :pt, :ecart, :com)
            """), {
                "fid":   facture_id,
                "lid":   ligne_id,
                "ref":   a.get("reference"),
                "des":   a.get("designation"),
                "type":  a.get("type_anomalie"),
                "pf":    a.get("prix_unitaire"),
                "pt":    a.get("prix_tarif"),
                "ecart": a.get("ecart_ht"),
                "com":   a.get("cause_anomalie")
            })

        db.commit()
        return facture_id
    finally:
        db.close()


# ── 4. Fonction principale ───────────────────────────────────
def traiter_facture(pdf_bytes: bytes, tarif: dict, nom_fichier: str) -> dict:
    """Point d'entrée principal de l'agent."""
    data     = analyser_facture_llm(pdf_bytes, tarif)
    type_doc = data.get("type_document", "facture")

    if type_doc in ("avoir", "rfa"):
        return {
            "facture_id":     None,
            "numero_facture": data.get("numero_facture"),
            "fournisseur":    data.get("fournisseur"),
            "client":         data.get("client"),
            "date_facture":   data.get("date_facture"),
            "montant_ht":     data.get("montant_ht"),
            "type_document":  type_doc,
            "nb_articles":    0,
            "nb_anomalies":   0,
            "anomalies":      [],
            "message":        f"Document ignoré — type : {type_doc.upper()}"
        }

    # ── Filtre sécurité — supprime anomalies incohérentes ────────
    anomalies_valides = []
    for a in data.get("anomalies", []):
        if a.get("type_anomalie") == "ECART_PRIX":
            pu_f = a.get("prix_unitaire") or 0
            pu_t = a.get("prix_tarif")    or 0
            # Écart réel uniquement si > 0.01€
            if pu_t and pu_f > pu_t + 0.01:
                anomalies_valides.append(a)
        else:
            anomalies_valides.append(a)
    data["anomalies"] = anomalies_valides

    facture_id = sauvegarder_facture(data, nom_fichier)
    return {
        "facture_id":     facture_id,
        "numero_facture": data.get("numero_facture"),
        "fournisseur":    data.get("fournisseur"),
        "client":         data.get("client"),
        "date_facture":   data.get("date_facture"),
        "montant_ht":     data.get("montant_ht"),
        "type_document":  type_doc,
        "nb_articles":    data.get("nb_articles", 0),
        "nb_anomalies":   len(data.get("anomalies", [])),
        "anomalies":      data.get("anomalies", [])
    }