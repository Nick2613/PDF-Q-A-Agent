import React, { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");

  // Convert frontend port → backend port
  const BACKEND = window.location.origin.replace(
    /-\d+\.app\.github\.dev/,
    "-8000.app.github.dev"
  );

  async function uploadPDF() {
    try {
      if (!file) {
        setStatus("Select a PDF first");
        return;
      }

      setStatus("Uploading PDF...");

      const form = new FormData();
      form.append("file", file);

      const r = await fetch(`${BACKEND}/upload_pdf`, {
        method: "POST",
        body: form
      });

      console.log("Upload status:", r.status);

      const data = await r.json();
      setStatus("PDF Uploaded. Chunks: " + data.chunks);
    } catch (e) {
      console.error("Upload error:", e);
      setStatus("Upload error: " + e.message);
    }
  }

  async function askQuestion() {
    try {
      if (!query.trim()) {
        setStatus("Enter a question.");
        return;
      }

      setStatus("Thinking...");

      const r = await fetch(`${BACKEND}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });

      console.log("Ask status:", r.status);

      const data = await r.json();
      setAnswer(data.answer);
      setStatus("Done.");
    } catch (e) {
      console.error("Ask error:", e);
      setStatus("Ask error: Failed to fetch");
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>PDF Q&A — Groq + RAG</h1>

      <input type="file" onChange={e => setFile(e.target.files[0])} />
      <button onClick={uploadPDF}>Upload PDF</button>

      <br /><br />

      <input
        placeholder="Ask a question..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        style={{ width: "350px" }}
      />
      <button onClick={askQuestion}>Ask</button>

      <h3>Status:</h3>
      <div>{status}</div>

      <h3>Answer:</h3>
      <pre>{answer}</pre>

      <p style={{ marginTop: "30px", fontSize: "12px" }}>
        Backend used: {BACKEND}
      </p>
    </div>
  );
}
