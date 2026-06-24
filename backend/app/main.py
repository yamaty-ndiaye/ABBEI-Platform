from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import assistant, agents, fichiers

app = FastAPI(
    title="ABBEI Platform API",
    description="Plateforme IA souveraine ABBEI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assistant.router, prefix="/api/assistant", tags=["Assistant IA"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents IA"])
app.include_router(fichiers.router, prefix="/api/fichiers", tags=["Fichiers"])

@app.get("/")
async def root():
    return {"message": "ABBEI Platform API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}