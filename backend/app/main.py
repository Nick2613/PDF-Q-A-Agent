import os
import fitz
import faiss
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()

# GitHub Codespaces requires these headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "*",
        "X-Forwarded-Host",
        "X-Forwarded-Port"
    ],
)

@app.get("/health")
def health():
    return {"message": "Backend is running"}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_EMBED_URL = "https://api.groq.com/openai/v1/embeddings"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

DIM = 1024
index = faiss.IndexFlatL2(DIM)
documents = []


def embed(text: str):
    r = requests.post(
        GROQ_EMBED_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": "nomic-embed-text", "input": text}
    )
    return np.array(r.json()["data"][0]["embedding"], dtype="float32")


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    global index, documents

    index = faiss.IndexFlatL2(DIM)
    documents = []

    pdf = fitz.open(stream=await file.read(), filetype="pdf")

    for page in pdf:
        text = page.get_text()
        if not text.strip():
            continue

        vector = embed(text)
        index.add(np.array([vector]))
        documents.append(text)

    return {"chunks": len(documents)}


@app.post("/ask")
async def ask(query: dict):
    q = query["query"]
    q_vec = embed(q)

    if index.ntotal == 0:
        return {"answer": "Upload a PDF first."}

    D, I = index.search(np.array([q_vec]), 3)
    retrieved = "\n".join([documents[i] for i in I[0] if i < len(documents)])

    prompt = f"Answer using this text:\n{retrieved}\n\nQuestion: {q}"

    r = requests.post(
        GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    return {"answer": r.json()["choices"][0]["message"]["content"]}
