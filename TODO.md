# Colruyt CodeMorph — Setup & Run Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | |
| Node.js | 18+ | For the React frontend |
| Groq API key | — | Free at https://console.groq.com |

## 1. Install Backend Dependencies

```bash
cd "4.Colruyt_Codemorph\backend"
pip install -r requirements.txt
```

## 2. Install Frontend Dependencies

```bash
cd ..\frontend
npm install
cd ..
```

## 3. Configure Backend Environment

```bash
copy backend\.env.example backend\.env
```

Edit `backend/.env`:

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# Optional tuning
CODEMORPH_MAX_CONCURRENT=4     # parallel file transformations
CODEMORPH_REQUEST_TIMEOUT=180  # seconds per LLM request
CODEMORPH_RETRY_CHUNK=8000     # chars per retry chunk on timeout
```

## 4. Initialize the Database

```bash
cd backend
python -c "from app.database.db import init_db; init_db()"
cd ..
```

## 5. Run the Backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: `http://localhost:8000/docs`

## 6. Run the Frontend

```bash
cd frontend
npm run dev
```

Opens at `http://localhost:5173`.

## 7. Usage

1. **Upload a codebase** (ZIP file) from the Projects page
2. **Configure the transformation** — select source stack (Java Spring, COBOL, etc.) and target stack (Python FastAPI, etc.)
3. **Run the pipeline** — the system:
   - Parses and analyses all source files
   - Extracts business rules before transformation
   - Rewrites each file using Groq with RAG context
   - Verifies functional equivalence of the transformed output
4. **Download the transformed ZIP** or browse files in the artifact viewer

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `groq.AuthenticationError` | Check `GROQ_API_KEY` in `backend/.env` |
| Transformation stuck in `pass-through` mode | GROQ_API_KEY missing; set it and restart |
| `langchain_groq` not found | Run `pip install langchain-groq` inside the backend folder |
| Frontend 502 on upload | Backend not running — start it first |
| Database error on startup | Delete `backend/codemorph.db` and restart to reinitialise |
