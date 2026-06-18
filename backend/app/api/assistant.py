from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.rag_pipeline import repondre

router = APIRouter()


# ============================================
# Modèles Pydantic
# ============================================

class QuestionRequest(BaseModel):
    texte: str
    utilisateur: str = "anonyme"


class Source(BaseModel):
    nom: str
    chemin: str
    lien: str | None = None


class ReponseResponse(BaseModel):
    question: str
    reponse: str
    sources: list[Source]


# ============================================
# Endpoints
# ============================================

@router.post("/question", response_model=ReponseResponse)
async def poser_question(question: QuestionRequest):
    result = repondre(question.texte)
    return ReponseResponse(
        question=result["question"],
        reponse=result["reponse"],
        sources=[Source(**s) for s in result["sources"]]
    )


@router.get("/health")
async def health():
    return {"status": "ok", "service": "assistant"}


@router.get("/stats")
async def stats():
    from app.agents.rag_pipeline import charger_vectorstore
    vs = charger_vectorstore()
    collection = vs.get()
    return {
        "chunks_total": len(collection["ids"]),
        "documents_uniques": len(set(m.get("nom") for m in collection["metadatas"]))
    }