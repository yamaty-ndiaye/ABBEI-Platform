# ABBEI Platform 🏗️

🇬🇧 [English version](README.md)

> Plateforme web souveraine pour ABBEI — association d'insertion spécialisée dans le second oeuvre du bâtiment.
> Intègre un assistant IA conversationnel, des pipelines de données automatisés et de la business intelligence.

---

## Architecture

| Couche | Technologie |
|---|---|
| API Backend | Python FastAPI |
| Base de données | PostgreSQL |
| Transformations SQL | dbt |
| Agents IA | LangChain + Ollama (Mistral) |
| Frontend | React |
| Orchestration | Airflow |
| Conteneurs | Docker Compose |

---

## Prérequis

- Docker Desktop avec WSL2
- Python 3.11+
- Node.js 20+

---

## Lancer le projet

    git clone https://github.com/yamaty-ndiaye/ABBEI-Platform.git
    cd ABBEI-Platform
    cp .env.example .env
    docker compose up -d

---

## Fonctionnalités principales

- **Assistant IA conversationnel** — interroger les données métiers en langage naturel
- **Ingestion PDF automatisée** — extraction et structuration des bons de commande
- **Tableaux de bord métiers** — activité, facturation, RH, planning
- **Stack souveraine** — 100% open source, auto-hébergeable, conforme RGPD

---

*Projet de stage — ESIGELEC x ABBEI — 2025*
