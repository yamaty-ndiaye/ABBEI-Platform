# ============================================================
# Routes FastAPI — Agents métiers
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Endpoints pour l'agent de contrôle factures
#              fournisseurs (upload tarif + analyse PDF)
# ============================================================

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.agents.invoice_agent import charger_tarif, traiter_facture
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request

router = APIRouter()

# Stockage temporaire du tarif en mémoire (par fournisseur)
tarifs_en_memoire: dict = {}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "agents"}


# ── 1. Upload tarif Excel ────────────────────────────────────
@router.post("/tarif/upload")
async def upload_tarif(
    fichier: UploadFile = File(...),
    fournisseur: str = Form(...),
    annee: int = Form(...)
):
    """
    Charge un fichier Excel tarif fournisseur.
    Le tarif est sauvegardé en base ET gardé en mémoire
    pour les analyses de la session.
    """
    if not fichier.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un Excel (.xlsx ou .xls)"
        )

    contenu = await fichier.read()

    try:
        tarif = charger_tarif(contenu, fournisseur, annee)
        tarifs_en_memoire[fournisseur] = tarif

        return {
            "message": f"Tarif {fournisseur} {annee} chargé avec succès",
            "fournisseur": fournisseur,
            "annee": annee,
            "nb_references": len(tarif)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture tarif : {str(e)}")


# ── 2. Analyse facture PDF ───────────────────────────────────
@router.post("/facture/analyser")
async def analyser_facture(
    fichier: UploadFile = File(...),
    fournisseur: str = Form(...)
):
    """
    Analyse un PDF facture fournisseur.
    Compare au tarif chargé en mémoire et détecte les anomalies.
    """
    if not fichier.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un PDF"
        )

    if fournisseur not in tarifs_en_memoire:
        raise HTTPException(
            status_code=400,
            detail=f"Tarif '{fournisseur}' non chargé. Uploadez d'abord le fichier Excel tarif."
        )

    contenu = await fichier.read()
    tarif = tarifs_en_memoire[fournisseur]

    try:
        resultat = traiter_facture(contenu, tarif, fichier.filename)
        return resultat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse facture : {str(e)}")


# ── 3. Liste des tarifs chargés ──────────────────────────────
@router.get("/tarifs")
async def liste_tarifs():
    """Retourne les tarifs actuellement chargés en mémoire."""
    return {
        "tarifs": [
            {"fournisseur": f, "nb_references": len(t)}
            for f, t in tarifs_en_memoire.items()
        ]
    }


# ── 4. Historique factures analysées ────────────────────────
@router.get("/factures")
async def liste_factures():
    """Retourne toutes les factures analysées depuis la base."""
    from sqlalchemy import text
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT f.id, f.numero_facture, f.fournisseur, f.client,
                   f.date_facture, f.montant_ht, f.created_at,
                   COUNT(a.id) as nb_anomalies
            FROM fournisseurs.factures f
            LEFT JOIN fournisseurs.anomalies a ON a.facture_id = f.id
            GROUP BY f.id
            ORDER BY f.created_at DESC
        """)).fetchall()

        return {
            "factures": [
                {
                    "id":             row[0],
                    "numero_facture": row[1],
                    "fournisseur":    row[2],
                    "client":         row[3],
                    "date_facture":   str(row[4]) if row[4] else None,
                    "montant_ht":     float(row[5]) if row[5] else None,
                    "created_at":     str(row[6]),
                    "nb_anomalies":   row[7]
                }
                for row in rows
            ]
        }
    finally:
        db.close()
# ── 5. Export Excel ──────────────────────────────────────────
@router.post("/factures/export")
async def export_excel(request: Request):
    """Génère et retourne un fichier Excel des anomalies."""
    from fastapi import Request
    from fastapi.responses import Response
    from app.agents.export_agent import generer_export_excel
    from datetime import date

    resultats = await request.json()
    fichier = generer_export_excel(resultats)
    nom = f"Anomalies_Factures_{date.today().strftime('%Y%m%d')}.xlsx"

    return Response(
        content=fichier,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nom}"}
    )