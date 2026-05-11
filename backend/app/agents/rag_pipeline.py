import os
import tempfile
from pathlib import Path
import pdfplumber
import fitz
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from app.agents.dropbox_connector import (
    get_client, lister_fichiers_dropbox, telecharger_fichier
)
from app.core.config import (
    OLLAMA_HOST, MISTRAL_MODEL, EMBEDDING_MODEL,
    DROPBOX_CHANTIERS_PATH,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS, SYSTEM_PROMPT
)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/chromadb")


def extraire_texte(tmp_path: str, extension: str) -> str:
    try:
        if extension == '.pdf':
            texte = ""
            # Essai 1 : pdfplumber
            try:
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            texte += t + "\n"
            except:
                pass

            # Essai 2 : PyMuPDF si pdfplumber échoue
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
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except:
                return ""
        else:
            return ""
    except Exception:
        return ""


def indexer_documents(chemin_dropbox: str = None, bailleur: str = None):
    chemin = chemin_dropbox or DROPBOX_CHANTIERS_PATH
    if bailleur:
        chemin = f"{chemin}/{bailleur}"

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
                doc = Document(
                    page_content=texte,
                    metadata={
                        "source": fichier["chemin"],
                        "nom": fichier["nom"],
                        "extension": fichier["extension"]
                    }
                )
                documents.append(doc)
            else:
                erreurs += 1
                print(f"  ❌ {fichier['nom']}: texte vide")

        except Exception as e:
            erreurs += 1
            print(f"  ❌ {fichier['nom']}: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if i % 20 == 0:
            print(f"  → {i}/{len(fichiers)} fichiers traités ({len(documents)} lisibles)...")

    print(f"✅ {len(documents)} documents extraits ({erreurs} erreurs)")

    if not documents:
        print("❌ Aucun document lisible")
        return None

    print("✂️  Découpage en chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ {len(chunks)} chunks créés")

    print("🧠 Création des embeddings avec nomic-embed-text...")
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_HOST
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    print(f"✅ Indexation terminée — {len(chunks)} chunks dans ChromaDB")
    return vectorstore


def charger_vectorstore():
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_HOST
    )
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )


def repondre(question: str) -> dict:
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
    indexer_documents(
        chemin_dropbox="/ABBEI/ChantiersABBEI/HABITAT 76",
        bailleur=None
    )