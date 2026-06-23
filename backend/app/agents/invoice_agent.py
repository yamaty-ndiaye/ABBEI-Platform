# ============================================================
# Agent — Contrôle factures fournisseurs
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Extraction PDF + comparaison tarif + détection
#              anomalies + insertion PostgreSQL
# ============================================================

import json
import base64
import pdfplumber
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
    Lit un fichier Excel tarif et retourne un dict {reference: {designation, prix}}
    Sauvegarde aussi le tarif en PostgreSQL pour historique.
    """
    wb = openpyxl.load_workbook(BytesIO(fichier_excel), data_only=True)
    ws = wb.active

    tarif = {}
    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip().lower() if h else "" for h in rows[0]]

    col_ref  = next((i for i, h in enumerate(headers) if "ref" in h or "article" in h or "code" in h), 0)
    col_des  = next((i for i, h in enumerate(headers) if "lib" in h or "desig" in h or "nom" in h), 1)
    col_prix = next((i for i, h in enumerate(headers) if "prix" in h or "p.u" in h or "tarif" in h), 2)

    for row in rows[1:]:
        ref  = str(row[col_ref]).strip()  if row[col_ref]  else None
        des  = str(row[col_des]).strip()  if row[col_des]  else None
        prix = row[col_prix]

        if ref and des and prix and ref != "None":
            try:
                tarif[ref] = {"designation": des, "prix": float(prix)}
            except (ValueError, TypeError):
                continue

    # Sauvegarde en base
    db = SessionLocal()
    try:
        for ref, data in tarif.items():
            db.execute(text("""
                INSERT INTO fournisseurs.tarifs
                    (fournisseur, annee, reference, designation, prix_unitaire)
                VALUES (:fournisseur, :annee, :ref, :des, :prix)
                ON CONFLICT (fournisseur, annee, reference) DO UPDATE
                SET designation   = EXCLUDED.designation,
                    prix_unitaire = EXCLUDED.prix_unitaire
            """), {"fournisseur": fournisseur, "annee": annee,
                   "ref": ref, "des": data["designation"], "prix": data["prix"]})
        db.commit()
    finally:
        db.close()

    return tarif


# ── 2. Extraction texte PDF (fallback) ───────────────────────
def extraire_texte_pdf(fichier_pdf: bytes) -> str:
    """
    Extrait le texte brut d'un PDF.
    Utilisé comme fallback si l'envoi direct à Claude échoue.
    """
    texte = ""
    try:
        with pdfplumber.open(BytesIO(fichier_pdf)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte += t + "\n"
    except Exception:
        pass
    return texte


# ── 3. Analyse LLM — PDF envoyé directement à Claude ────────
def analyser_facture_llm(texte_pdf: str, pdf_bytes: bytes = None) -> dict:
    """
    Envoie le PDF directement à Claude comme document base64.
    Beaucoup plus précis que pdfplumber sur les PDFs scannés.
    Si pdf_bytes est absent, utilise le texte extrait.
    """
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
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
                        "text": """Tu es un expert comptable. Analyse cette facture fournisseur.

Réponds UNIQUEMENT en JSON valide sans markdown :
{
  "numero_facture": "numéro de la facture",
  "fournisseur": "nom du fournisseur",
  "client": "nom du client destinataire",
  "date_facture": "YYYY-MM-DD ou null",
  "montant_ht": 0.00,
  "type_document": "facture ou avoir ou rfa",
  "lignes": [
    {
      "reference": "référence article ou null",
      "designation": "désignation du produit",
      "chantier": "référence chantier ex: STOCK, BOLBEC, QUEVILLY HABITAT ou null",
      "quantite": 0.00,
      "unite": "U, M2, ML, L, KG ou null",
      "prix_catalogue": 0.00,
      "remise_pct": 0.00,
      "prix_unitaire": 0.00,
      "montant_ht": 0.00
    }
  ]
}

RÈGLES :
- Ignore les lignes éco-participation et surcoût énergétique
- Le chantier est souvent indiqué comme Réf. XXXX ou BL N° XXXX ou nom du site
- Si type_document est avoir ou rfa ne cherche pas d anomalies
- Si une info est absente mets null
- Montants en euros HT, date format YYYY-MM-DD
- Extrais TOUTES les lignes articles sans exception"""
                    }
                ]
            }]
        )
    else:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""Tu es un expert comptable. Analyse ce texte de facture fournisseur.

TEXTE :
{texte_pdf}

Réponds UNIQUEMENT en JSON valide sans markdown :
{{
  "numero_facture": "numéro",
  "fournisseur": "nom",
  "client": "nom",
  "date_facture": "YYYY-MM-DD ou null",
  "montant_ht": 0.00,
  "type_document": "facture ou avoir ou rfa",
  "lignes": [
    {{
      "reference": "référence ou null",
      "designation": "désignation",
      "chantier": "chantier ou null",
      "quantite": 0.00,
      "unite": "U, M2, ML, L, KG ou null",
      "prix_catalogue": 0.00,
      "remise_pct": 0.00,
      "prix_unitaire": 0.00,
      "montant_ht": 0.00
    }}
  ]
}}

RÈGLES : ignore éco-participation et surcoût énergétique, montants en euros HT."""
            }]
        )

    texte = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(texte)


# ── 4. Détection anomalies ───────────────────────────────────
def detecter_anomalies(lignes: list, tarif: dict) -> list:
    """Compare chaque ligne au tarif et retourne les anomalies."""
    anomalies = []
    for ligne in lignes:
        ref         = ligne.get("reference")
        designation = ligne.get("designation", "")
        pu_facture  = ligne.get("prix_unitaire") or 0
        quantite    = ligne.get("quantite") or 0

        if not ref:
            continue

        if ref in tarif:
            pu_tarif = tarif[ref]["prix"]
            if pu_facture > pu_tarif:
                ecart = round((pu_facture - pu_tarif) * quantite, 2)
                anomalies.append({
                    "reference":    ref,
                    "designation":  designation,
                    "type_anomalie": "ECART_PRIX",
                    "prix_facture": pu_facture,
                    "prix_tarif":   pu_tarif,
                    "ecart_ht":     ecart,
                    "commentaire":  f"Facturé {pu_facture}€ vs tarif {pu_tarif}€ (+{ecart}€ HT)"
                })
        else:
            anomalies.append({
                "reference":    ref,
                "designation":  designation,
                "type_anomalie": "HORS_BORDEREAU",
                "prix_facture": pu_facture,
                "prix_tarif":   None,
                "ecart_ht":     round(pu_facture * quantite, 2),
                "commentaire":  f"Référence {ref} absente du bordereau"
            })
    return anomalies


# ── 5. Sauvegarde PostgreSQL ─────────────────────────────────
def sauvegarder_facture(data: dict, anomalies: list, nom_fichier: str) -> int:
    """Insère la facture, ses lignes et ses anomalies en base."""
    db = SessionLocal()
    try:
        # Facture
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

        # Lignes + anomalies
        for ligne in data.get("lignes", []):
            res_ligne = db.execute(text("""
                INSERT INTO fournisseurs.lignes_facture
                    (facture_id, reference, designation, quantite, prix_unitaire, montant_ht)
                VALUES (:fid, :ref, :des, :qte, :pu, :ht)
                RETURNING id
            """), {
                "fid": facture_id,
                "ref": ligne.get("reference"),
                "des": ligne.get("designation"),
                "qte": ligne.get("quantite"),
                "pu":  ligne.get("prix_unitaire"),
                "ht":  ligne.get("montant_ht")
            })
            ligne_id = res_ligne.fetchone()[0]

            anomalie = next(
                (a for a in anomalies if a["reference"] == ligne.get("reference")), None
            )
            if anomalie:
                db.execute(text("""
                    INSERT INTO fournisseurs.anomalies
                        (facture_id, ligne_id, reference, designation, type_anomalie,
                         prix_facture, prix_tarif, ecart_ht, commentaire)
                    VALUES (:fid, :lid, :ref, :des, :type, :pf, :pt, :ecart, :com)
                """), {
                    "fid":   facture_id, "lid":  ligne_id,
                    "ref":   anomalie["reference"],
                    "des":   anomalie["designation"],
                    "type":  anomalie["type_anomalie"],
                    "pf":    anomalie["prix_facture"],
                    "pt":    anomalie["prix_tarif"],
                    "ecart": anomalie["ecart_ht"],
                    "com":   anomalie["commentaire"]
                })

        db.commit()
        return facture_id
    finally:
        db.close()


# ── 6. Fonction principale ───────────────────────────────────
def traiter_facture(pdf_bytes: bytes, tarif: dict, nom_fichier: str) -> dict:
    """Point d'entrée principal de l'agent."""
    texte      = extraire_texte_pdf(pdf_bytes)
    data       = analyser_facture_llm(texte, pdf_bytes)
    
    # Si c'est un avoir ou une RFA → pas d'analyse tarifaire
    type_doc = data.get("type_document", "facture")
    if type_doc in ("avoir", "rfa"):
        return {
            "facture_id":     None,
            "numero_facture": data.get("numero_facture"),
            "fournisseur":    data.get("fournisseur"),
            "date_facture":   data.get("date_facture"),
            "montant_ht":     data.get("montant_ht"),
            "type_document":  type_doc,
            "nb_lignes":      0,
            "nb_anomalies":   0,
            "anomalies":      [],
            "message":        f"Document ignoré — type : {type_doc.upper()}"
        }

    anomalies  = detecter_anomalies(data.get("lignes", []), tarif)
    facture_id = sauvegarder_facture(data, anomalies, nom_fichier)

    return {
        "facture_id":     facture_id,
        "numero_facture": data.get("numero_facture"),
        "fournisseur":    data.get("fournisseur"),
        "date_facture":   data.get("date_facture"),
        "montant_ht":     data.get("montant_ht"),
        "type_document":  type_doc,
        "nb_lignes":      len(data.get("lignes", [])),
        "nb_anomalies":   len(anomalies),
        "anomalies":      anomalies
    }