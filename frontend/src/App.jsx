import React, { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState("");

  async function upload() {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${API}/upload_pdf`, { method: "POST", body: fd });
    alert(JSON.stringify(await r.json()));
  }

  async function ask() {
    const fd = new FormData();
    fd.append("question", q);
    const r = await fetch(`${API}/ask`, { method: "POST", body: fd });
    const j = await r.json();
    setAnswer(j.answer);
  }

  return (
    <div className="box">
      <h2>PDF Q&A — Groq + RAG</h2>

      <input type="file" onChange={e=>setFile(e.target.files[0])} />
      <button onClick={upload}>Upload</button>

      <textarea rows="3" placeholder="Ask" value={q} onChange={e=>setQ(e.target.value)}></textarea>
      <button onClick={ask}>Ask</button>

      <pre>{answer}</pre>
    </div>
  );
}
