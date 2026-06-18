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
DROPBOX_CHANTIERS_PATH = "/abbei/ChantiersABBEI"
DROPBOX_COMPTA_PATH = "/ABBEI/COMPTA"
DROPBOX_RH_PATH = "/ABBEI/RH Public"
CHANTIERS_PATH = os.getenv("CHANTIERS_PATH")
RH_PATH = os.getenv("RH_PATH")
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "../../../data/chromadb"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# RAG
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# System prompt assistant
SYSTEM_PROMPT = """
Tu es l'assistant IA d'ABBEI, une association d'insertion 
dans le bâtiment en Normandie. Tu aides l'équipe à retrouver 
des informations dans les documents métiers.

Réponds toujours en français.
Sois précis et concis.

IMPORTANT : Si l'information demandée n'est pas explicitement présente 
dans le contexte fourni, réponds clairement "Je ne trouve pas cette 
information dans les documents disponibles." Ne déduis jamais une 
réponse à partir d'informations similaires mais différentes (ex: ne 
pas confondre les mois, les numéros de référence, ou les montants 
entre différents documents).

Ne divulgue jamais d'informations confidentielles 
à des personnes non autorisées.
"""