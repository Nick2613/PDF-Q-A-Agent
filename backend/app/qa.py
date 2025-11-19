import os
import aiohttp
from embeddings_store import VectorStore
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "mixtral-8x7b-32768"   # or llama3-8b

class QAEngine:
    def __init__(self, vs: VectorStore):
        self.vs = vs

    async def ask_groq(self, prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You answer using only the provided context."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "max_tokens": 300
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_URL, headers=headers, json=payload) as res:
                data = await res.json()
                return data["choices"][0]["message"]["content"]

    async def answer(self, question):
        hits = self.vs.search(question, k=5)
        context = "\n\n".join(hits)

        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer only from the context. "
            "If not found, say: Answer not found in document."
        )

        reply = await self.ask_groq(prompt)
        return {"answer": reply, "sources": hits}
