import React, { useState } from 'react';
import './App.css';

// Point to the backend URL
const API_URL = "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Please select a file");
    
    const formData = new FormData();
    formData.append("file", file);
    setUploadStatus("Uploading...");

    try {
      const res = await fetch(`${API_URL}/upload_pdf`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setUploadStatus(`✅ ${data.message}`);
      setChatHistory([]); // Reset chat on new file
    } catch (error) {
      setUploadStatus("❌ Upload failed");
      console.error(error);
    }
  };

  const handleAsk = async () => {
    if (!question) return;
    
    const newHistory = [...chatHistory, { role: 'user', content: question }];
    setChatHistory(newHistory);
    setQuestion("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question }),
      });
      const data = await res.json();
      setChatHistory([...newHistory, { role: 'bot', content: data.answer, sources: data.sources }]);
    } catch (error) {
      setChatHistory([...newHistory, { role: 'bot', content: "Error getting answer." }]);
    }
    setIsLoading(false);
  };

  return (
    <div className="app-container">
      <header>
        <h1>📄 PDF Multilingual Chatbot</h1>
      </header>

      <div className="upload-section">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button onClick={handleUpload}>Upload PDF</button>
        <p className="status">{uploadStatus}</p>
      </div>

      <div className="chat-section">
        <div className="messages">
          {chatHistory.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong>
              <p>{msg.content}</p>
              {msg.sources && (
                <details>
                  <summary>View Sources</summary>
                  <p className="source-text">{msg.sources}</p>
                </details>
              )}
            </div>
          ))}
          {isLoading && <div className="message bot">Thinking...</div>}
        </div>

        <div className="input-area">
          <input 
            type="text" 
            value={question} 
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
            placeholder="Ask a question about the PDF..." 
          />
          <button onClick={handleAsk}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;