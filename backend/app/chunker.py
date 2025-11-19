import re

def simple_clean(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text, size=500, overlap=100):
    text = simple_clean(text)
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunk = " ".join(tokens[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks
