from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

MODEL = "all-mpnet-base-v2"

class VectorStore:
    def __init__(self, path="vs_store"):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.model = SentenceTransformer(MODEL)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadatas = []
        self._load()

    def add(self, chunks):
        embs = self.model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        if embs.dtype != "float32":
            embs = embs.astype("float32")

        self.index.add(embs)
        self.metadatas.extend(chunks)
        self._save()

    def search(self, query, k=5):
        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        D, I = self.index.search(q.astype("float32"), k)
        results = []
        for idx in I[0]:
            if idx < len(self.metadatas):
                results.append(self.metadatas[idx])
        return results

    def _save(self):
        faiss.write_index(self.index, f"{self.path}/index.faiss")
        with open(f"{self.path}/meta.pkl", "wb") as f:
            pickle.dump(self.metadatas, f)

    def _load(self):
        try:
            self.index = faiss.read_index(f"{self.path}/index.faiss")
            with open(f"{self.path}/meta.pkl", "rb") as f:
                self.metadatas = pickle.load(f)
        except:
            pass
