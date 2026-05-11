# ABBEI Platform 🏗️

🇫🇷 [Version française](README.fr.md)

> Sovereign web platform for ABBEI — a French insertion association specialized in building trades.
> Integrates a conversational AI assistant powered by RAG, automated data pipelines, and business intelligence.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend API | Python FastAPI |
| Database | PostgreSQL 16 |
| Vector Store | ChromaDB → Qdrant (planned) |
| Embeddings | nomic-embed-text via Ollama |
| LLM | Mistral 7B via Ollama |
| RAG Orchestration | LangChain |
| Document Storage | Dropbox API → Nextcloud (planned) |
| SQL Transformations | dbt |
| Frontend | React |
| Orchestration | Airflow |
| Containers | Docker Compose |

---

## Prerequisites

- Docker Desktop with WSL2
- Python 3.11+
- Node.js 20+
- Dropbox API token

---

## Getting Started

    git clone https://github.com/yamaty-ndiaye/ABBEI-Platform.git
    cd ABBEI-Platform
    cp .env.example .env
    # Add your credentials in .env
    docker compose up -d postgres ollama
    cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m app.agents.rag_pipeline

---

## Key Features

- **Conversational AI assistant** — query Dropbox documents in natural language via RAG
- **Dropbox API integration** — reads all files directly from the cloud, no local sync needed
- **Multi-format extraction** — PDF, Word, Excel documents
- **Automated PDF ingestion** — extract and structure purchase orders and invoices
- **Business dashboards** — activity, billing, HR, planning
- **Sovereign stack** — fully open source, self-hostable, GDPR compliant

---

## Project Structure

    ABBEI-Platform/
    backend/
        app/
            agents/         RAG pipeline, Dropbox connector
            api/            FastAPI routes
            core/           Config, database
            models/         SQLAlchemy models
            schemas/        Pydantic schemas
        dbt/                SQL transformations
    frontend/               React interface
    data/                   ChromaDB vector store
    docs/                   Technical documentation

---

## Current Status

- PostgreSQL 16 with 4 schemas and 6 tables
- RAG pipeline fully operational on Dropbox files
- Mistral 7B + nomic-embed-text running locally via Ollama
- 559 chunks indexed from HABITAT 76 documents

## Roadmap

- FastAPI REST endpoints
- React chat interface
- Nextcloud migration (sovereign storage)
- Qdrant migration (scalable vector store)
- RAGAS evaluation framework

---

## Built With

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![LangChain](https://img.shields.io/badge/LangChain-latest-green)
![Ollama](https://img.shields.io/badge/Ollama-Mistral7B-orange)

---

*Internship project — ESIGELEC x ABBEI — 2025/2026*
