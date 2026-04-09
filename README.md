# ABBEI Platform 🏗️

🇫🇷 [Version française](README.fr.md)

> Sovereign web platform for ABBEI — a French insertion association specialized in building trades.
> Integrates a conversational AI assistant, automated data pipelines, and business intelligence.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend API | Python FastAPI |
| Database | PostgreSQL |
| SQL Transformations | dbt |
| AI Agents | LangChain + Ollama (Mistral) |
| Frontend | React |
| Orchestration | Airflow |
| Containers | Docker Compose |

---

## Prerequisites

- Docker Desktop with WSL2
- Python 3.11+
- Node.js 20+

---

## Getting Started

    git clone https://github.com/yamaty-ndiaye/ABBEI-Platform.git
    cd ABBEI-Platform
    cp .env.example .env
    docker compose up -d

---

## Key Features

- **Conversational AI assistant** — query business data in natural language
- **Automated PDF ingestion** — extract and structure purchase orders
- **Business dashboards** — activity, billing, HR, planning
- **Sovereign stack** — fully open source, self-hostable, GDPR compliant

---

## Built With

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

*Internship project — ESIGELEC x ABBEI — 2025*
