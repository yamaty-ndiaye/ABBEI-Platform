import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# ABBEI Platform — Configuration centrale
# ============================================

# Base de données
DATABASE_URL = (
    f"postgresql://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Ollama / Mistral
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11435")
MISTRAL_MODEL = "mistral"
EMBEDDING_MODEL = "nomic-embed-text"

# Dropbox
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_CHANTIERS_PATH = "/ABBEI/ChantiersABBEI"
DROPBOX_COMPTA_PATH = "/ABBEI/COMPTA"
DROPBOX_RH_PATH = "/ABBEI/RH Public"
CHANTIERS_PATH = os.getenv("CHANTIERS_PATH")
RH_PATH = os.getenv("RH_PATH")

# RAG
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K_RESULTS = 5

# System prompt assistant
SYSTEM_PROMPT = """
Tu es l'assistant IA d'ABBEI, une association d'insertion 
dans le bâtiment en Normandie. Tu aides l'équipe à retrouver 
des informations dans les documents métiers.

Réponds toujours en français.
Sois précis et concis.
Si tu ne trouves pas l'information, dis-le clairement.
Ne divulgue jamais d'informations confidentielles 
à des personnes non autorisées.
"""