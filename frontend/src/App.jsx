import { useState } from "react"
import Chat from "./components/Chat"
import InvoiceAgent from "./components/InvoiceAgent"

const ONGLETS = [
  { id: "chat",    label: "💬 Assistant IA",          badge: "RAG" },
  { id: "factures",label: "⚡ Contrôle Factures",     badge: "Agent" },
]

function App() {
  const [ongletActif, setOngletActif] = useState("chat")

  return (
    <div style={{
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      fontFamily: "system-ui, sans-serif"
    }}>
      {/* ── Header ── */}
      <div style={{
        padding: "0 1.5rem",
        borderBottom: "1px solid #e2e8f0",
        display: "flex",
        alignItems: "center",
        gap: "1.5rem"
      }}>
        {/* Logo */}
        <span style={{ fontSize: "18px", fontWeight: "600", padding: "1rem 0",
          color: "#1e293b", whiteSpace: "nowrap" }}>
          🏗️ ABBEI Platform
        </span>

        {/* Onglets */}
        <div style={{ display: "flex", gap: 4, flex: 1 }}>
          {ONGLETS.map(({ id, label, badge }) => (
            <button
              key={id}
              onClick={() => setOngletActif(id)}
              style={{
                padding: "0.75rem 1.25rem",
                border: "none",
                borderBottom: ongletActif === id
                  ? "2px solid #2563eb"
                  : "2px solid transparent",
                background: "none",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: ongletActif === id ? 600 : 400,
                color: ongletActif === id ? "#2563eb" : "#64748b",
                display: "flex",
                alignItems: "center",
                gap: 8,
                transition: "all 0.15s"
              }}
            >
              {label}
              <span style={{
                fontSize: "11px",
                background: ongletActif === id ? "#dbeafe" : "#f1f5f9",
                color: ongletActif === id ? "#1d4ed8" : "#94a3b8",
                padding: "1px 8px",
                borderRadius: 999
              }}>
                {badge}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Contenu ── */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {ongletActif === "chat"     && <Chat />}
        {ongletActif === "factures" && <InvoiceAgent />}
      </div>
    </div>
  )
}

export default App