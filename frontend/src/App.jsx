import { useState } from "react";

const API = import.meta.env.VITE_API_URL;

function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  async function upload() {
    if (!file) {
      setAnswer("Select a PDF first.");
      return;
    }

    const data = new FormData();
    data.append("file", file);

    const res = await fetch(`${API}/upload_pdf`, {
      method: "POST",
      body: data
    });

    const json = await res.json();
    setAnswer(`Uploaded and indexed: ${json.chunks} chunks`);
  }

  async function ask() {
    if (!question.trim()) {
      setAnswer("Enter a question.");
      return;
    }

    const res = await fetch(`${API}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question })
    });

    const json = await res.json();
    setAnswer(json.answer);
  }

  return (
    <div style={{ width: "80%", margin: "30px auto", fontFamily: "Arial" }}>
      <h1>PDF Q&A — Groq + RAG</h1>

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={upload} style={{ marginLeft: "10px" }}>Upload</button>

      <br /><br />

      <textarea
        placeholder="Ask something from the PDF..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows="3"
        style={{ width: "100%" }}
      />

      <br /><br />
      <button onClick={ask}>Ask</button>

      <div style={{
        background: "#f0f0f0",
        padding: "15px",
        marginTop: "20px",
        minHeight: "40px"
      }}>
        {answer}
      </div>
    </div>
  );
}

export default App;
