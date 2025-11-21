import os
import fitz  # PyMuPDF
import faiss
import numpy as np
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import pathlib

# 1. CONFIG & SETUP
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEYS
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# MODEL
print("Loading embedding model...")
embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
EMBED_DIM = 384

# --- STATE MANAGEMENT (Fixes the memory issue) ---
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

# 2. UI INTERFACE
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Chatbot v2</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .box { margin-bottom: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; }
            button { padding: 12px 24px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 6px; font-size: 16px; transition: background 0.3s; }
            button:hover { background: #0056b3; }
            input[type="text"] { width: 70%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
            .chat-entry { margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }
            .user { color: #007bff; font-weight: bold; margin-bottom: 5px; }
            .bot { color: #333; line-height: 1.6; }
            .sources { font-size: 0.85em; color: #666; background: #eee; padding: 10px; border-radius: 5px; margin-top: 10px; display: none; }
            .toggle-source { color: #666; cursor: pointer; font-size: 0.8em; text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>🤖 PDF Intelligent Chatbot</h1>
        
        <div class="container">
            <!-- UPLOAD -->
            <div class="box">
                <h3>1. Upload Document</h3>
                <p style="font-size:0.9em; color: #666;">Current File: <span id="currentFile">None</span></p>
                <input type="file" id="pdfFile">
                <button onclick="uploadPDF()">Upload & Reset</button>
                <div id="uploadStatus" style="margin-top:10px; font-weight:bold;"></div>
            </div>

            <!-- CHAT -->
            <div class="box">
                <h3>2. Ask Question</h3>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="question" placeholder="e.g., Summarize the main points..." onkeypress="handleEnter(event)">
                    <button onclick="askQuestion()">Ask</button>
                </div>
            </div>

            <div id="chat-history"></div>
        </div>

        <script>
            function handleEnter(e) { if(e.key === 'Enter') askQuestion(); }

            async function uploadPDF() {
                const fileInput = document.getElementById('pdfFile');
                const status = document.getElementById('uploadStatus');
                
                if (!fileInput.files[0]) { alert("Select a file!"); return; }

                status.innerText = "⏳ Processing... Clearing old memory...";
                status.style.color = "orange";

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                try {
                    const res = await fetch('/upload_pdf', { method: 'POST', body: formData });
                    const data = await res.json();
                    status.innerText = "✅ " + data.message;
                    status.style.color = "green";
                    document.getElementById('currentFile').innerText = data.filename;
                    document.getElementById('chat-history').innerHTML = ""; // Clear chat
                } catch (e) {
                    status.innerText = "❌ Upload failed.";
                    status.style.color = "red";
                }
            }

            async function askQuestion() {
                const qInput = document.getElementById('question');
                const q = qInput.value;
                const history = document.getElementById('chat-history');
                
                if (!q) return;
                qInput.value = ""; // Clear input

                const id = Date.now();
                
                // Add User Message
                const userDiv = `<div class="chat-entry"><div class="user">👤 You: ${q}</div><div class="bot" id="bot-${id}">⏳ Thinking...</div></div>`;
                history.insertAdjacentHTML('afterbegin', userDiv);

                try {
                    const res = await fetch('/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: q })
                    });
                    const data = await res.json();
                    
                    // Update Bot Message
                    const botDiv = document.getElementById(`bot-${id}`);
                    botDiv.innerHTML = `
                        🤖 <strong>AI:</strong> ${data.answer}
                        <br><br>
                        <span class="toggle-source" onclick="document.getElementById('src-${id}').style.display = 'block'">Show Context Used</span>
                        <div id="src-${id}" class="sources"><strong>Excerpts used:</strong><br>${data.sources}</div>
                    `;
                } catch (e) {
                    document.getElementById(`bot-${id}`).innerText = "❌ Error connecting to server.";
                }
            }
        </script>
    </body>
    </html>
    """

# 3. BACKEND LOGIC

def create_chunks(text, chunk_size=800, overlap=200):
    """Larger chunks (800) with overlap (200) to keep context together."""
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
        if len(chunk) > 50: # Ignore tiny chunks
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # 1. RESET STATE
    state.reset()
    state.filename = file.filename
    
    # 2. READ PDF
    try:
        doc = fitz.open(stream=await file.read(), filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid PDF")

    if not full_text.strip():
        return {"message": "PDF is empty or scanned image.", "filename": file.filename}

    # 3. CHUNK & EMBED
    chunks = create_chunks(full_text)
    state.chunks = chunks

    if chunks:
        embeddings = embed_model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        state.index.add(embeddings)

    return {
        "message": f"Success! Learned {len(chunks)} text chunks from {file.filename}.",
        "filename": file.filename
    }

@app.post("/ask")
async def ask(payload: dict):
    query = payload.get("query")
    
    if state.index.ntotal == 0:
        return {"answer": "Please upload a PDF first.", "sources": "None"}

    # 1. SEARCH
    q_vec = embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = state.index.search(q_vec, k=5) # Get top 5 chunks

    # 2. RETRIEVE CONTEXT
    retrieved_texts = []
    for idx in indices[0]:
        if 0 <= idx < len(state.chunks):
            retrieved_texts.append(state.chunks[idx])
    
    context_block = "\n\n---\n\n".join(retrieved_texts)

    # 3. ASK GROQ
    prompt = f"""
    You are an expert assistant. Answer the question based ONLY on the context provided below.
    
    Context from Document:
    {context_block}
    
    Question: {query}
    
    Instructions:
    - If the answer is in the context, explain it clearly.
    - If the answer is NOT in the context, say "I cannot find this information in the document."
    """

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1 
    }

    try:
        r = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
        r.raise_for_status() # Raise error if 400/401/500
        ans = r.json()["choices"][0]["message"]["content"]
        
        # Escape HTML for safe display in "Sources"
        safe_source = context_block.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        
        return {"answer": ans, "sources": safe_source}
    except Exception as e:
        print(f"Groq Error: {e}")
        if 'r' in locals(): print(r.text)
        return {"answer": "Error connecting to AI model.", "sources": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}