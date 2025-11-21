PDF-Q/A-Agent
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       └── __init__.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── App.css

📖 How to Run the PDF Q&A Agent

This project uses Docker to run a Python Backend (FastAPI) and a React Frontend (Vite) simultaneously.

1. Prerequisites

Before starting, ensure you have the following installed:

Docker Desktop (or Docker Engine)

Git

A Groq API Key (Get one for free at console.groq.com)

2. Clone the Repository

code
Bash
download
content_copy
expand_less
git clone https://github.com/YOUR_USERNAME/PDF-Q-A-Agent.git
cd PDF-Q-A-Agent

3. Setup Environment Variables

Create a .env file in the root directory (/PDF-Q-A-Agent/.env) to store your API key.

Create the file:

Mac/Linux: touch .env

Windows: Right-click -> New Text File -> Name it .env

Open the file and add your key:

code
Env
download
content_copy
expand_less
GROQ_API_KEY=gsk_yoursuperlongkeyhere...

4. Configure the Frontend Connection

⚠️ This is the most important step.

You need to tell the Frontend (React) where the Backend (Python) is living.

Option A: Running Locally (On your Laptop)

If you are running this on your own machine, you likely do not need to change anything.

Open frontend/src/App.jsx.

Ensure line 5 looks like this:

code
JavaScript
download
content_copy
expand_less
const API_URL = "http://localhost:8000";
Option B: Running in GitHub Codespaces (Cloud)

If you are running in a cloud environment, localhost will not work.

Run the app once to generate the URLs (see Step 5 below), then check the PORTS tab in VS Code.

Find Port 8000 -> Right Click -> Port Visibility -> Public.

Copy the "Forwarded Address" (e.g., https://your-app-8000.github.dev).

Open frontend/src/App.jsx.

Update the line with your copied URL (remove any trailing /):

code
JavaScript
download
content_copy
expand_less
const API_URL = "https://your-app-8000.github.dev";

5. Build and Run

Open your terminal in the project root and run:

code
Bash
download
content_copy
expand_less
docker-compose up --build

Wait a few minutes for the first build (it needs to download the AI models).

Once you see Uvicorn running on http://0.0.0.0:8000, the app is ready.

6. How to Use

Open your browser:

Local: Go to http://localhost:3000

Codespaces: Click the link for Port 3000 in the Ports tab.

Upload a PDF: Click "Choose File" and "Upload". Wait for the "✅ Success" message.

Ask Questions: Type your question in the chat box and hit Send.

🛑 Troubleshooting

"Upload Failed" or Network Error?

This usually means the Frontend cannot find the Backend.

Check: Did you set the API_URL in frontend/src/App.jsx correctly?

Check: If using Codespaces, did you set Port 8000 to Public?

Fix: After changing App.jsx, you must stop the server (Ctrl+C) and rebuild:

code
Bash
download
content_copy
expand_less
docker-compose up --build

"Model Decommissioned" Error?

Open backend/app/main.py.

Search for model and ensure it is set to a supported version like llama-3.3-70b-versatile.