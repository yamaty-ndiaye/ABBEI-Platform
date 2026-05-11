import os
import shutil
import tempfile
from pathlib import Path
import pdfplumber
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from app.core.config import (
    OLLAMA_HOST, MISTRAL_MODEL, CHANTIERS_PATH,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS, SYSTEM_PROMPT
)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/chromadb")
EXTENSIONS_UTILES = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}
DOSSIERS_CIBLES = [
    "GestionBonsCdes", "Facturation",
    "BON FACTURES", "BONS ANNULES", "BT finis"
]


def lister_fichiers(chemin: str) -> list:
    """Liste tous les fichiers utiles dans les dossiers ciblés"""
    fichiers = []
    path = Path(chemin)

    for f in path.rglob('*'):
        if f.is_file() and f.suffix.lower() in EXTENSIONS_UTILES:
            fichiers.append(str(f))

    print(f"✅ {len(fichiers)} fichiers trouvés")
    return fichiers


def extraire_texte(fichier: str) -> str:
    """Extrait le texte en copiant d'abord dans /tmp pour éviter les problèmes WSL"""
    ext = Path(fichier).suffix.lower()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        shutil.copy2(fichier, tmp_path)

        if ext == '.pdf':
            with pdfplumber.open(tmp_path) as pdf:
                texte = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texte += t + "\n"
            return texte

        elif ext in ['.docx', '.doc']:
            try:
                doc = DocxDocument(tmp_path)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except:
                return ""
        else:
            return ""

    except Exception:
        return ""
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


def indexer_documents(chemin: str = None):
    """Indexe les documents dans ChromaDB"""
    chemin = chemin or CHANTIERS_PATH
    print(f"🔍 Indexation depuis : {chemin}")

    fichiers = lister_fichiers(chemin)
    if not fichiers:
        print("❌ Aucun fichier trouvé")
        return None

    print("📄 Chargement des documents...")
    documents = []
    erreurs = 0
    for i, fichier in enumerate(fichiers):
        texte = extraire_texte(fichier)
        if texte.strip():
            doc = Document(
                page_content=texte,
                metadata={
                    "source": fichier,
                    "bailleur": Path(fichier).parts[-4] if len(Path(fichier).parts) >= 4 else "inconnu"
                }
            )
            documents.append(doc)
        else:
            erreurs += 1
        if i % 50 == 0:
            print(f"  → {i}/{len(fichiers)} fichiers traités...")

    print(f"✅ {len(documents)} documents chargés ({erreurs} fichiers vides/erreurs)")

    if not documents:
        print("❌ Aucun document lisible trouvé")
        return None

    print("✂️  Découpage en chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ {len(chunks)} chunks créés")

    print("🧠 Création des embeddings...")
    embeddings = OllamaEmbeddings(
        model=MISTRAL_MODEL,
        base_url=OLLAMA_HOST
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    print(f"✅ Indexation terminée — {len(chunks)} chunks stockés dans ChromaDB")
    return vectorstore


def charger_vectorstore():
    """Charge le vectorstore existant"""
    embeddings = OllamaEmbeddings(
        model=MISTRAL_MODEL,
        base_url=OLLAMA_HOST
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )


def repondre(question: str) -> dict:
    """Répond à une question en utilisant le RAG"""
    vectorstore = charger_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K_RESULTS})

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=f"""{SYSTEM_PROMPT}

Contexte extrait des documents ABBEI :
{{context}}

Question : {{question}}

Réponse :"""
    )

    llm = Ollama(model=MISTRAL_MODEL, base_url=OLLAMA_HOST)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    sources = retriever.invoke(question)
    reponse = chain.invoke(question)

    return {
        "question": question,
        "reponse": reponse,
        "sources": [doc.metadata.get("source", "inconnu") for doc in sources]
    }


if __name__ == "__main__":
    chemin_test = "/mnt/c/Users/stagiaire/ABBEI Dropbox/ABBEI/COMPTA"
    indexer_documents(chemin_test)