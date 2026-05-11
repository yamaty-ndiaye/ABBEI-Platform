# ABBEI Platform 🏗️

🇬🇧 [English version](README.md)

> Plateforme web souveraine pour ABBEI — association d'insertion spécialisée dans le second œuvre du bâtiment.
> Intègre un assistant IA conversationnel basé sur le RAG, des pipelines de données automatisés et de la business intelligence.

---

## Architecture

| Couche | Technologie |
|---|---|
| API Backend | Python FastAPI |
| Base de données | PostgreSQL 16 |
| Base vectorielle | ChromaDB → Qdrant (prévu) |
| Embeddings | nomic-embed-text via Ollama |
| LLM | Mistral 7B via Ollama |
| Orchestration RAG | LangChain |
| Stockage documents | API Dropbox → Nextcloud (prévu) |
| Transformations SQL | dbt |
| Frontend | React |
| Orchestration | Airflow |
| Conteneurs | Docker Compose |

---

## Prérequis

- Docker Desktop avec WSL2
- Python 3.11+
- Node.js 20+
- Token API Dropbox

---

## Lancer le projet

    git clone https://github.com/yamaty-ndiaye/ABBEI-Platform.git
    cd ABBEI-Platform
    cp .env.example .env
    # Remplir les credentials dans .env
    docker compose up -d postgres ollama
    cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m app.agents.rag_pipeline

---

## Fonctionnalités principales

- **Assistant IA conversationnel** — interroger les documents Dropbox en langage naturel via RAG
- **Intégration API Dropbox** — lit tous les fichiers directement depuis le cloud
- **Extraction multi-formats** — PDFs, Word, Excel
- **Ingestion PDF automatisée** — extraction des bons de commande et factures
- **Tableaux de bord métiers** — activité, facturation, RH, planning
- **Stack souveraine** — 100% open source, auto-hébergeable, conforme RGPD

---

## Structure du projet

    ABBEI-Platform/
    backend/
        app/
            agents/         Pipeline RAG, connecteur Dropbox
            api/            Routes FastAPI
            core/           Config, base de données
            models/         Modèles SQLAlchemy
            schemas/        Schémas Pydantic
        dbt/                Transformations SQL
    frontend/               Interface React
    data/                   Base vectorielle ChromaDB
    docs/                   Documentation technique

---

## État actuel

- PostgreSQL 16 avec 4 schémas et 6 tables
- Pipeline RAG opérationnel sur les fichiers Dropbox
- Mistral 7B + nomic-embed-text en local via Ollama
- 559 chunks indexés depuis les documents HABITAT 76

## Feuille de route

- Endpoints REST FastAPI
- Interface de chat React
- Migration Nextcloud (stockage souverain)
- Migration Qdrant (base vectorielle scalable)
- Framework d'évaluation RAGAS

---

*Projet de stage — ESIGELEC x ABBEI — 2025/2026*
