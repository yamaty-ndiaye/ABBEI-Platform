# ============================================================
# Export Excel — Résultats agent factures fournisseurs
# Projet     : ABBEI Platform
# Date       : 2026-06-23
# Description: Génère un fichier Excel structuré avec :
#              - Onglet Anomalies (détail par facture)
#              - Onglet Récapitulatif (synthèse)
#              - Onglet Comparaison (si 2 fournisseurs)
# ============================================================

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import date

# ── Constantes couleurs ──────────────────────────────────────
BLEU_FONCE  = "1E3A5F"
BLEU_MOYEN  = "2563EB"
BLANC       = "FFFFFF"
ROUGE_CLAIR = "FFDEDE"
ROUGE_TEXTE = "C0392B"
JAUNE_CLAIR = "FFF3CD"
JAUNE_TEXTE = "856404"
VERT_CLAIR  = "D4EDDA"
VERT_TEXTE  = "155724"
GRIS_CLAIR  = "F8F9FA"
GRIS_LIGNE  = "E9ECEF"
ORANGE      = "E67E22"


def _thin_border():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)


def _style_header(cell, bg=BLEU_FONCE, fg=BLANC, size=11, center=True):
    cell.font = Font(bold=True, color=fg, size=size, name="Arial")
    cell.fill = PatternFill("solid", start_color=bg)
    cell.alignment = Alignment(
        horizontal="center" if center else "left",
        vertical="center", wrap_text=True
    )
    cell.border = _thin_border()


def _style_cell(cell, bg=None, bold=False, color="000000",
                center=False, italic=False):
    cell.font = Font(bold=bold, color=color, size=10,
                     name="Arial", italic=italic)
    if bg:
        cell.fill = PatternFill("solid", start_color=bg)
    cell.alignment = Alignment(
        horizontal="center" if center else "left",
        vertical="center", wrap_text=True
    )
    cell.border = _thin_border()


# ── Onglet 1 : Anomalies détaillées ─────────────────────────
def _creer_onglet_anomalies(wb, resultats: list):
    ws = wb.active
    ws.title = "Anomalies"

    # Titre
    ws.merge_cells("A1:J1")
    titre = ws["A1"]
    titre.value = f"CONTRÔLE FACTURES FOURNISSEURS — ANOMALIES DÉTECTÉES — {date.today().strftime('%d/%m/%Y')}"
    _style_header(titre, size=13)
    ws.row_dimensions[1].height = 28

    # Sous-titre stats
    total_factures  = len(resultats)
    total_anomalies = sum(r.get("nb_anomalies", 0) for r in resultats)
    total_ecart     = sum(
        a.get("ecart_ht", 0) or 0
        for r in resultats
        for a in r.get("anomalies", [])
        if a.get("type_anomalie") == "ECART_PRIX"
    )

    ws.merge_cells("A2:J2")
    sous = ws["A2"]
    sous.value = (f"{total_factures} facture(s) analysée(s)  ·  "
                  f"{total_anomalies} anomalie(s) détectée(s)  ·  "
                  f"Surcoût cumulé : {total_ecart:.2f} € HT")
    sous.font = Font(italic=True, size=10, color="555555", name="Arial")
    sous.alignment = Alignment(horizontal="center", vertical="center")
    sous.fill = PatternFill("solid", start_color=GRIS_CLAIR)
    ws.row_dimensions[2].height = 18

    # En-têtes colonnes
    headers = [
        "N° Facture", "Fournisseur", "Client", "Date",
        "Type anomalie", "Référence", "Désignation",
        "P.U. facturé", "P.U. tarif", "Écart HT"
    ]
    col_widths = [16, 18, 20, 12, 18, 18, 40, 13, 13, 13]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=3, column=col, value=h)
        _style_header(cell, bg="2563EB")
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[3].height = 22

    # Données
    row = 4
    for r in resultats:
        anomalies = r.get("anomalies", [])
        if not anomalies:
            # Ligne verte : facture conforme
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                _style_cell(cell, bg=VERT_CLAIR)
            ws.cell(row=row, column=1).value = r.get("numero_facture", "—")
            ws.cell(row=row, column=2).value = r.get("fournisseur", "—")
            ws.cell(row=row, column=3).value = r.get("client", "—")
            ws.cell(row=row, column=4).value = r.get("date_facture", "—")
            ws.cell(row=row, column=5).value = "✅ Conforme"
            ws.cell(row=row, column=5).font = Font(
                bold=True, color=VERT_TEXTE, name="Arial", size=10)
            row += 1
            continue

        for a in anomalies:
            is_ecart = a.get("type_anomalie") == "ECART_PRIX"
            bg = JAUNE_CLAIR if is_ecart else ROUGE_CLAIR
            bg_alt = "FFFBF0" if is_ecart else "FFF5F5"

            valeurs = [
                r.get("numero_facture", "—"),
                r.get("fournisseur", "—"),
                r.get("client", "—"),
                r.get("date_facture", "—"),
                "⚠ ÉCART PRIX" if is_ecart else "✘ HORS BORDEREAU",
                a.get("reference", "—"),
                a.get("designation", "—"),
                a.get("prix_facture"),
                a.get("prix_tarif"),
                a.get("ecart_ht"),
            ]

            for col, val in enumerate(valeurs, 1):
                cell = ws.cell(row=row, column=col, value=val)
                use_bg = bg if col == 5 else (bg_alt if row % 2 == 0 else BLANC)
                _style_cell(cell, bg=use_bg)

                # Style colonne type
                if col == 5:
                    cell.font = Font(
                        bold=True, size=10, name="Arial",
                        color=JAUNE_TEXTE if is_ecart else ROUGE_TEXTE
                    )
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # Format monétaire
                if col in (8, 9, 10) and isinstance(val, (int, float)):
                    cell.number_format = '#,##0.00 "€"'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    if col == 10 and val and val > 0:
                        cell.font = Font(bold=True, color=ROUGE_TEXTE,
                                         size=10, name="Arial")

            row += 1

    # Figer la ligne d'en-tête
    ws.freeze_panes = "A4"

    # Total écart en bas
    if total_ecart > 0:
        row += 1
        ws.merge_cells(f"A{row}:I{row}")
        cell_label = ws[f"A{row}"]
        cell_label.value = "TOTAL SURCOÛT HT"
        _style_header(cell_label, bg=ROUGE_TEXTE, size=11)

        cell_total = ws[f"J{row}"]
        cell_total.value = total_ecart
        cell_total.number_format = '#,##0.00 "€"'
        _style_header(cell_total, bg=ROUGE_TEXTE, size=11)


# ── Onglet 2 : Récapitulatif par facture ────────────────────
def _creer_onglet_recap(wb, resultats: list):
    ws = wb.create_sheet("Récapitulatif")

    ws.merge_cells("A1:G1")
    titre = ws["A1"]
    titre.value = "RÉCAPITULATIF PAR FACTURE"
    _style_header(titre, size=13)
    ws.row_dimensions[1].height = 28

    headers = [
        "N° Facture", "Fournisseur", "Client",
        "Date", "Montant HT", "Nb anomalies", "Statut"
    ]
    col_widths = [18, 18, 22, 13, 15, 15, 20]

    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=2, column=col, value=h)
        _style_header(cell, bg="2563EB")
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[2].height = 22

    for i, r in enumerate(resultats, 1):
        nb = r.get("nb_anomalies", 0)
        bg = GRIS_CLAIR if i % 2 == 0 else BLANC
        valeurs = [
            r.get("numero_facture", "—"),
            r.get("fournisseur", "—"),
            r.get("client", "—"),
            r.get("date_facture", "—"),
            r.get("montant_ht"),
            nb,
            "✅ Conforme" if nb == 0 else f"⚠ {nb} anomalie(s)",
        ]
        for col, val in enumerate(valeurs, 1):
            cell = ws.cell(row=i + 2, column=col, value=val)
            _style_cell(cell, bg=bg)
            if col == 5 and isinstance(val, (int, float)):
                cell.number_format = '#,##0.00 "€"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if col == 7:
                cell.font = Font(
                    bold=True, size=10, name="Arial",
                    color=VERT_TEXTE if nb == 0 else ROUGE_TEXTE
                )
                cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.freeze_panes = "A3"


# ── Fonction principale ──────────────────────────────────────
def generer_export_excel(resultats: list) -> bytes:
    """
    Génère le fichier Excel complet à partir des résultats de l'agent.
    Retourne les bytes du fichier prêt à télécharger.
    """
    wb = openpyxl.Workbook()

    _creer_onglet_anomalies(wb, resultats)
    _creer_onglet_recap(wb, resultats)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()