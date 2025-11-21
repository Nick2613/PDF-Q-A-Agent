import os
import fitz  # PyMuPDF
import faiss
import numpy as np
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow Frontend to talk to Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIG
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
EMBED_DIM = 384

print("Loading embedding model...")
embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# STATE MANAGEMENT
class AppState:
    def __init__(self):
        self.index = faiss.IndexFlatIP(EMBED_DIM)
        self.chunks = []
        self.filename = "None"

    def reset(self):
        self.index = faiss.IndexFlatIP(EMBED_DIM)
        self.chunks = []
        self.filename = "None"

state = AppState()

# LOGIC: CHUNKING
def create_chunks(text, chunk_size=800, overlap=200):
    text_len = len(text)
    chunks = []
    start = 0
    while start < text_len:
        end = start + chunk_size
        if end < text_len:
            last_space = text.rfind(' ', start, end)
            if last_space != -1 and last_space > start:
                end = last_space
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

# API ROUTES
@app.get("/health")
def health():
    return {"status": "backend_running"}

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    state.reset()
    state.filename = file.filename
    
    try:
        doc = fitz.open(stream=await file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF")

    if not full_text.strip():
        return {"message": "Empty PDF", "filename": file.filename}

    chunks = create_chunks(full_text)
    state.chunks = chunks

    if chunks:
        embeddings = embed_model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        state.index.add(embeddings)

    return {"message": f"Processed {len(chunks)} chunks.", "filename": file.filename}

@app.post("/ask")
async def ask(payload: dict):
    query = payload.get("query")
    if state.index.ntotal == 0:
        return {"answer": "Please upload a PDF first.", "sources": ""}

    q_vec = embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = state.index.search(q_vec, k=5)

    retrieved_texts = [state.chunks[i] for i in indices[0] if 0 <= i < len(state.chunks)]
    context_block = "\n\n---\n\n".join(retrieved_texts)

    prompt = f"""
    Context:
    {context_block}
    
    Question: {query}
    
    Answer using ONLY the context. If not found, say "I cannot find this info."
    """

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    json_body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        r = requests.post(GROQ_CHAT_URL, headers=headers, json=json_body)
        r.raise_for_status()
        return {"answer": r.json()["choices"][0]["message"]["content"], "sources": context_block}
    except Exception as e:
        return {"answer": "Error connecting to AI.", "sources": str(e)}