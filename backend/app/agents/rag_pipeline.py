import os
import shutil
from pathlib import Path
import pdfplumber
import fitz
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
import anthropic
from app.agents.dropbox_connector import (
    get_client, lister_fichiers_dropbox, telecharger_fichier, generer_lien
)
from app.core.config import (
    OLLAMA_HOST, MISTRAL_MODEL, EMBEDDING_MODEL,
    DROPBOX_CHANTIERS_PATH, CHROMA_PATH,
    CHUNK_SIZE, CHUNK_OVERLAP, SYSTEM_PROMPT,
    ANTHROPIC_API_KEY, CLAUDE_MODEL
)


# ============================================
# Extraction de texte
# ============================================

def extraire_texte(tmp_path: str, extension: str) -> str:
    """Extrait le texte d'un fichier selon son extension"""
    try:
        if extension == '.pdf':
            texte = ""
            try:
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            texte += t + "\n"
            except:
                pass
            if not texte.strip():
                try:
                    doc = fitz.open(tmp_path)
                    for page in doc:
                        texte += page.get_text()
                except:
                    pass
            return texte

        elif extension in ['.docx', '.doc']:
            try:
                doc = DocxDocument(tmp_path)
                texte = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                if texte.strip():
                    return texte
                import docx2txt
                return docx2txt.process(tmp_path) or ""
            except:
                try:
                    import docx2txt
                    return docx2txt.process(tmp_path) or ""
                except:
                    return ""

        elif extension in ['.xlsx', '.xls']:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(tmp_path)
                texte = ""
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        ligne = " ".join([str(c) for c in row if c is not None])
                        if ligne.strip():
                            texte += ligne + "\n"
                return texte
            except:
                return ""

        elif extension == '.pptx':
            try:
                from pptx import Presentation
                prs = Presentation(tmp_path)
                texte = ""
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            texte += shape.text + "\n"
                return texte
            except:
                return ""

        else:
            return ""
    except Exception:
        return ""


# ============================================
# Détection du type de document
# ============================================

def detecter_type(nom: str) -> str:
    """Détecte le type de document selon son nom"""
    nom_lower = nom.lower()
    if any(x in nom_lower for x in ['facture', 'f150206', 'f240', 'f260']):
        return "facture"
    elif any(x in nom_lower for x in ['bc.', 'bt.', 'otms', 'otsol', 'otpeint', 'otdgs']):
        return "bon_commande"
    elif any(x in nom_lower for x in ['o02', 'o03', 'o04', 'o05', 'ar-09', 'ar-10', 'ar-13']):
        return "administratif"
    else:
        return "autre"


def detecter_filtre(question: str) -> dict:
    """Détecte si on doit filtrer par type de document"""
    q = question.lower()
    if any(x in q for x in ['facture', 'montant', 'ttc', 'ht', 'tva', 'paiement']):
        return {"type": "facture"}
    elif any(x in q for x in ['bon de commande', 'bc', 'intervention', 'bt']):
        return {"type": "bon_commande"}
    return {}


# ============================================
# Indexation
# ============================================

def indexer_documents(chemin_dropbox: str = None, reset: bool = False):
    """Indexe les documents depuis Dropbox dans ChromaDB"""
    chemin = chemin_dropbox or DROPBOX_CHANTIERS_PATH

    if reset and os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("🗑️ ChromaDB réinitialisée")

    print(f"🔍 Indexation depuis Dropbox : {chemin}")

    dbx = get_client()
    fichiers = lister_fichiers_dropbox(dbx, chemin)
    print(f"✅ {len(fichiers)} fichiers trouvés")

    if not fichiers:
        print("❌ Aucun fichier trouvé")
        return None

    print("📄 Extraction du texte...")
    documents = []
    erreurs = 0

    for i, fichier in enumerate(fichiers):
        tmp_path = None
        try:
            tmp_path = telecharger_fichier(dbx, fichier["chemin"])
            texte = extraire_texte(tmp_path, fichier["extension"])

            if texte.strip():
                documents.append(Document(
                    page_content=texte,
                    metadata={
                        "source": fichier["chemin"],
                        "nom": fichier["nom"],
                        "extension": fichier["extension"],
                        "type": detecter_type(fichier["nom"])
                    }
                ))
            else:
                erreurs += 1

        except Exception as e:
            erreurs += 1
            print(f"  ❌ {fichier['nom']}: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if i % 20 == 0:
            print(f"  → {i}/{len(fichiers)} traités ({len(documents)} lisibles)...")

    print(f"✅ {len(documents)} documents extraits ({erreurs} erreurs)")

    if not documents:
        print("❌ Aucun document lisible")
        return None

    print("✂️  Découpage en chunks (adaptatif)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = []
    for doc in documents:
        if len(doc.page_content) < 2000:
            chunks.append(doc)
        else:
            chunks.extend(splitter.split_documents([doc]))

    print(f"✅ {len(chunks)} chunks créés")

    print("🧠 Création des embeddings...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f"✅ Indexation terminée — {len(chunks)} chunks dans ChromaDB")
    return vectorstore


# ============================================
# Chargement du vectorstore
# ============================================

def charger_vectorstore():
    """Charge le vectorstore existant"""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST)
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)


# ============================================
# Reranker (singleton)
# ============================================

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


# ============================================
# Réponse RAG
# ============================================

def repondre(question: str) -> dict:
    """Répond à une question via RAG avec reranking et Claude"""
    vectorstore = charger_vectorstore()

    # 1. Détecter le filtre selon le type de question
    filtre = detecter_filtre(question)
    if filtre:
        chunks = vectorstore.similarity_search(question, k=20, filter=filtre)
        if not chunks:
            chunks = vectorstore.similarity_search(question, k=50)
    else:
        chunks = vectorstore.similarity_search(question, k=50)

    if not chunks:
        return {
            "question": question,
            "reponse": "Aucun document indexé pour répondre à cette question.",
            "sources": []
        }

    # 2. Dédupliquer — garder le meilleur chunk par document
    chunks_dedupliques = []
    sources_vues = set()
    for chunk in chunks:
        nom = chunk.metadata.get("nom", "")
        if nom not in sources_vues:
            chunks_dedupliques.append(chunk)
            sources_vues.add(nom)

    # 3. Reranking sur les chunks dédupliqués
    reranker = get_reranker()
    scores = reranker.predict(
        [(question, chunk.page_content) for chunk in chunks_dedupliques]
    )

    # 4. Garder les 3 meilleurs
    chunks_tries = [chunk for _, chunk in
                    sorted(zip(scores, chunks_dedupliques), key=lambda x: x[0], reverse=True)][:3]

    # 5. Construire le prompt et appeler Claude
    contexte = "\n\n".join([c.page_content for c in chunks_tries])

    prompt_text = f"""{SYSTEM_PROMPT}

Contexte extrait des documents ABBEI :
{contexte}

Question : {question}

Réponse :"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt_text}]
    )
    reponse = message.content[0].text

    # 6. Générer les liens Dropbox pour les sources
    dbx = get_client()
    sources = []
    vus = set()
    for chunk in chunks_tries:
        chemin = chunk.metadata.get("source", "")
        if chemin in vus:
            continue
        vus.add(chemin)
        nom = chunk.metadata.get("nom", chemin)
        lien = generer_lien(dbx, chemin) if chemin.lower().startswith("/abbei") else None
        sources.append({
            "nom": nom,
            "chemin": chemin,
            "lien": lien
        })

    return {
        "question": question,
        "reponse": reponse,
        "sources": sources
    }


if __name__ == "__main__":
    indexer_documents(
        chemin_dropbox="/abbei/ChantiersABBEI/HABITAT 76/Y-PE010Y-H76-MarchéEntretien",
        reset=True
    )