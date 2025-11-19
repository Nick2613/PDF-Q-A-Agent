import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from .pdf_extract import extract_text_from_pdf
from .chunker import chunk_text
from .embeddings_store import VectorStore
from .qa import QAEngine
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

os.makedirs("uploads", exist_ok=True)

vs = VectorStore("vs_store")
qa = QAEngine(vs)

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text_from_pdf(path)
    chunks = chunk_text(text)
    vs.add(chunks)

    return {"status": "indexed", "chunks": len(chunks)}

@app.post("/ask")
async def ask(question: str = Form(...)):
    return await qa.answer(question)

@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
