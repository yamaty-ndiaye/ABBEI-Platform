import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('../.env')

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import OllamaLLM, OllamaEmbeddings

from app.agents.rag_pipeline import charger_vectorstore, repondre
from app.core.config import OLLAMA_HOST, MISTRAL_MODEL, EMBEDDING_MODEL

# Dataset de test — questions avec réponses attendues
test_data = [
    {
        "question": "Quel est le montant TTC de la facture de janvier 2024 pour HABITAT 76 ?",
        "ground_truth": "Le montant TTC de la facture de janvier 2024 est indiqué dans la facture N° 150206_2024_1."
    },
    {
        "question": "Quels bons de commande sont associés au marché MA-2023-052A ?",
        "ground_truth": "Les bons de commande associés au marché MA-2023-052A sont référencés dans les documents ABBEI."
    },
    {
        "question": "Quelle est l'adresse de HABITAT 76 ?",
        "ground_truth": "HABITAT 76 est situé au 112 Boulevard d'Orléans, 76100 Rouen."
    }
]

# Récupérer les contextes depuis ChromaDB
vectorstore = charger_vectorstore()

questions = []
answers = []
contexts = []
ground_truths = []

for item in test_data:
    question = item["question"]
    
    # Récupérer les chunks
    docs = vectorstore.similarity_search(question, k=5)
    context = [doc.page_content for doc in docs]
    
    # Obtenir la réponse
    result = repondre(question)
    
    questions.append(question)
    answers.append(result["reponse"])
    contexts.append(context)
    ground_truths.append(item["ground_truth"])
    
    print(f"✅ Question traitée : {question[:50]}...")

# Créer le dataset RAGAS
dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths
})

# Configurer Ollama comme LLM pour RAGAS
llm = LangchainLLMWrapper(OllamaLLM(model=MISTRAL_MODEL, base_url=OLLAMA_HOST))
embeddings = LangchainEmbeddingsWrapper(OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST))

# Évaluer
print("\n🔍 Évaluation RAGAS en cours...")
results = evaluate(
    dataset=dataset,
    metrics=[
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy
    ],
    llm=llm,
    embeddings=embeddings
)

print("\n📊 Résultats RAGAS :")
print(results)
df = results.to_pandas()
print(df.to_string())
