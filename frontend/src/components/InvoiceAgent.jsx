// ============================================================
// Composant — Agent Contrôle Factures Fournisseurs
// Projet     : ABBEI Platform
// Date       : 2026-06-23
// Description: Interface drag & drop pour upload tarif Excel
//              et analyse des factures PDF fournisseurs
// ============================================================

import { useState, useCallback, useRef } from "react";

const API_URL = "http://localhost:8000/api/agents";

export default function InvoiceAgent() {
  const [fournisseur, setFournisseur]     = useState("");
  const [annee, setAnnee]                 = useState(2026);
  const [tarifCharge, setTarifCharge]     = useState(null);
  const [resultats, setResultats]         = useState([]);
  const [loadingTarif, setLoadingTarif]   = useState(false);
  const [loadingPdf, setLoadingPdf]       = useState(false);
  const [dragging, setDragging]           = useState(false);
  const [erreur, setErreur]               = useState(null);
  const inputTarifRef                     = useRef();
  const inputPdfRef                       = useRef();

  // ── Upload tarif Excel ──────────────────────────────────
  const uploadTarif = async (fichier) => {
    if (!fournisseur.trim()) {
      setErreur("Renseigne le nom du fournisseur avant d'uploader le tarif.");
      return;
    }
    setLoadingTarif(true);
    setErreur(null);

    const formData = new FormData();
    formData.append("fichier", fichier);
    formData.append("fournisseur", fournisseur);
    formData.append("annee", annee);

    try {
      const res  = await fetch(`${API_URL}/tarif/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setTarifCharge(data);
    } catch (e) {
      setErreur("Erreur upload tarif : " + e.message);
    } finally {
      setLoadingTarif(false);
    }
  };

  // ── Analyse facture PDF ─────────────────────────────────
  const analyserFacture = async (fichier) => {
    if (!tarifCharge) {
      setErreur("Charge d'abord un tarif Excel avant d'analyser une facture.");
      return;
    }
    setLoadingPdf(true);
    setErreur(null);

    const formData = new FormData();
    formData.append("fichier", fichier);
    formData.append("fournisseur", fournisseur);

    try {
      const res  = await fetch(`${API_URL}/facture/analyser`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setResultats(r => [data, ...r]);
    } catch (e) {
      setErreur("Erreur analyse facture : " + e.message);
    } finally {
      setLoadingPdf(false);
    }
  };

  // ── Drag & Drop PDF ─────────────────────────────────────
  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const fichiers = [...e.dataTransfer.files].filter(f => f.name.endsWith(".pdf"));
    fichiers.forEach(analyserFacture);
  }, [tarifCharge, fournisseur]);

  // ── Stats globales ───────────────────────────────────────
  const totalAnomalies  = resultats.reduce((s, r) => s + (r.nb_anomalies || 0), 0);
  const totalEcartPrix  = resultats.reduce((s, r) => s + (r.anomalies || [])
    .filter(a => a.type_anomalie === "ECART_PRIX")
    .reduce((ss, a) => ss + (a.ecart_ht || 0), 0), 0);

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: "0 auto", fontFamily: "Segoe UI, sans-serif" }}>

      {/* ── Titre ── */}
      <h2 style={{ marginBottom: 24, color: "#1e293b" }}>
        ⚡ Agent Contrôle Factures Fournisseurs
      </h2>

      {/* ── Erreur ── */}
      {erreur && (
        <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", borderRadius: 8,
          padding: "12px 16px", marginBottom: 20, color: "#991b1b" }}>
          ⚠️ {erreur}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>

        {/* ── Étape 1 : Tarif ── */}
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 20 }}>
          <h3 style={{ marginBottom: 16, color: "#334155", fontSize: 15 }}>
            📋 Étape 1 — Charger le tarif
          </h3>

          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", fontSize: 13, color: "#64748b", marginBottom: 4 }}>
              Fournisseur
            </label>
            <input
              value={fournisseur}
              onChange={e => setFournisseur(e.target.value)}
              placeholder="ex: OSCA, PPG..."
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8,
                border: "1px solid #cbd5e1", fontSize: 14 }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, color: "#64748b", marginBottom: 4 }}>
              Année
            </label>
            <input
              type="number"
              value={annee}
              onChange={e => setAnnee(parseInt(e.target.value))}
              style={{ width: "100%", padding: "8px 12px", borderRadius: 8,
                border: "1px solid #cbd5e1", fontSize: 14 }}
            />
          </div>

          <input ref={inputTarifRef} type="file" accept=".xlsx,.xls"
            style={{ display: "none" }}
            onChange={e => e.target.files[0] && uploadTarif(e.target.files[0])} />

          <button
            onClick={() => inputTarifRef.current.click()}
            disabled={loadingTarif}
            style={{ width: "100%", padding: "10px", borderRadius: 8,
              background: loadingTarif ? "#94a3b8" : "#3b82f6",
              color: "white", border: "none", cursor: "pointer", fontSize: 14 }}>
            {loadingTarif ? "⏳ Chargement..." : "📂 Uploader le tarif Excel"}
          </button>

          {tarifCharge && (
            <div style={{ marginTop: 12, background: "#dcfce7", border: "1px solid #86efac",
              borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#166534" }}>
              ✅ {tarifCharge.fournisseur} {tarifCharge.annee} —{" "}
              <strong>{tarifCharge.nb_references} références</strong> chargées
            </div>
          )}
        </div>

        {/* ── Étape 2 : Factures ── */}
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0",
          borderRadius: 12, padding: 20 }}>
          <h3 style={{ marginBottom: 16, color: "#334155", fontSize: 15 }}>
            📄 Étape 2 — Analyser les factures
          </h3>

          {/* Zone drag & drop */}
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => inputPdfRef.current.click()}
            style={{
              border: `2px dashed ${dragging ? "#3b82f6" : "#cbd5e1"}`,
              borderRadius: 10, padding: "32px 16px", textAlign: "center",
              cursor: "pointer", background: dragging ? "#eff6ff" : "white",
              transition: "all 0.2s"
            }}>
            <input ref={inputPdfRef} type="file" accept=".pdf" multiple
              style={{ display: "none" }}
              onChange={e => [...e.target.files].forEach(analyserFacture)} />
            <div style={{ fontSize: 32, marginBottom: 8 }}>
              {loadingPdf ? "⏳" : "📂"}
            </div>
            <div style={{ fontSize: 14, color: "#64748b" }}>
              {loadingPdf
                ? "Analyse en cours..."
                : "Glissez vos factures PDF ici ou cliquez"}
            </div>
            <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
              Plusieurs fichiers acceptés
            </div>
          </div>

          {/* Stats */}
          {resultats.length > 0 && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
              gap: 10, marginTop: 14 }}>
              {[
                { label: "Factures",  val: resultats.length, color: "#3b82f6" },
                { label: "Anomalies", val: totalAnomalies,   color: "#ef4444" },
                { label: "Surcoût HT",val: totalEcartPrix.toFixed(2) + " €", color: "#f59e0b" },
              ].map(({ label, val, color }) => (
                <div key={label} style={{ background: "white", border: "1px solid #e2e8f0",
                  borderRadius: 8, padding: "10px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color }}>{val}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
{/* ── Bouton Export Excel ── */}
      {resultats.length > 0 && (
        <div style={{ textAlign: "right", marginBottom: 16 }}>
          <button
            onClick={async () => {
              const res = await fetch(`${API_URL}/factures/export`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(resultats)
              });
              const blob = await res.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `Anomalies_Factures_${new Date().toISOString().slice(0,10)}.xlsx`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            style={{
              background: "#16a34a", color: "white", border: "none",
              borderRadius: 8, padding: "10px 20px", cursor: "pointer",
              fontSize: 14, fontWeight: 600
            }}>
            📥 Télécharger Excel
          </button>
        </div>
      )}

      {/* ── Résultats ── */}
      {resultats.map((r, idx) => (
        <div key={idx} style={{ background: "white", border: "1px solid #e2e8f0",
          borderRadius: 12, marginBottom: 16, overflow: "hidden" }}>

          {/* En-tête facture */}
          <div style={{ background: "#f1f5f9", padding: "12px 20px",
            display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ fontWeight: 700, color: "#1e293b" }}>
              {r.numero_facture || "Facture"}
            </span>
            <span style={{ fontSize: 13, color: "#64748b" }}>{r.fournisseur}</span>
            <span style={{ fontSize: 13, color: "#64748b" }}>{r.date_facture}</span>
            <span style={{ marginLeft: "auto", fontSize: 13, fontWeight: 600 }}>
              {r.montant_ht} € HT
            </span>
            <span style={{
              background: r.nb_anomalies > 0 ? "#fee2e2" : "#dcfce7",
              color: r.nb_anomalies > 0 ? "#991b1b" : "#166534",
              border: `1px solid ${r.nb_anomalies > 0 ? "#fca5a5" : "#86efac"}`,
              borderRadius: 20, padding: "2px 12px", fontSize: 12, fontWeight: 600
            }}>
              {r.nb_anomalies} anomalie{r.nb_anomalies > 1 ? "s" : ""}
            </span>
          </div>

          {/* Tableau anomalies */}
          {r.anomalies?.length > 0 ? (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#f8fafc" }}>
                  {["Type", "Référence", "Désignation", "P.U. facturé", "P.U. tarif", "Écart HT"].map(h => (
                    <th key={h} style={{ padding: "10px 16px", textAlign: "left",
                      color: "#64748b", fontWeight: 600, fontSize: 12,
                      borderBottom: "1px solid #e2e8f0" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {r.anomalies.map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ padding: "10px 16px" }}>
                      <span style={{
                        background: a.type_anomalie === "ECART_PRIX" ? "#fef3c7" : "#fee2e2",
                        color: a.type_anomalie === "ECART_PRIX" ? "#92400e" : "#991b1b",
                        borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 700
                      }}>
                        {a.type_anomalie === "ECART_PRIX" ? "⚠ ÉCART PRIX" : "✘ HORS BORDEREAU"}
                      </span>
                    </td>
                    <td style={{ padding: "10px 16px", color: "#64748b", fontFamily: "monospace" }}>
                      {a.reference}
                    </td>
                    <td style={{ padding: "10px 16px", color: "#334155" }}>{a.designation}</td>
                    <td style={{ padding: "10px 16px", color: a.type_anomalie === "ECART_PRIX" ? "#b45309" : "#334155" }}>
                      {a.prix_facture} €
                    </td>
                    <td style={{ padding: "10px 16px", color: "#64748b" }}>
                      {a.prix_tarif ? a.prix_tarif + " €" : "—"}
                    </td>
                    <td style={{ padding: "10px 16px", color: "#ef4444", fontWeight: 600 }}>
                      {a.ecart_ht > 0 ? "+" + a.ecart_ht + " €" : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: "16px 20px", color: "#16a34a", fontSize: 13 }}>
              ✅ Tous les articles sont conformes au tarif.
            </div>
          )}
        </div>
      ))}
    </div>
  );
}