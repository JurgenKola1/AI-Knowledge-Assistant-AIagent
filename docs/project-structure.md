# Project Structure

Clear map of the AI Knowledge Assistant as it is set up now.

---

## Folder tree

```
AI Knowledge Assistant Agent/
│
├── app.py                      # Main entry point - Flask routes
├── requirements.txt            # Python packages
├── README.md                   # Project overview
├── LICENSE
├── LumaMark_LX500_Test_Manual.pdf  # Sample fictional test manual
├── .env                        # Your API keys (local only, not committed)
├── .env.example                # Template for API keys
├── .gitignore
│
├── backend/                    # Server logic
│   ├── config.py               # Settings, models, allowed file types
│   ├── database.py             # SQLite document list
│   ├── prompts/                # AI prompt text
│   │   ├── chat.py             # Orchestrator, grounded answer, app-help prompts
│   │   └── vision.py           # Image / scanned PDF text extraction prompt
│   └── services/
│       ├── upload.py           # Save file → extract → store
│       ├── extract.py          # Read text from PDF / Word / images
│       ├── search.py           # Pinecone embed + search
│       └── conversation.py     # Chat: orchestrator + grounded answers
│
├── templates/
│   └── index.html              # Web page layout
│
├── static/
│   ├── css/
│   │   └── style.css           # Page styling
│   └── js/
│       └── app.js              # Upload, chat UI, session memory
│
├── docs/
│   ├── setup.md                # Install and run
│   ├── how-it-works.md         # Upload + chat flow
│   ├── customize.md            # Change prompts, models, branding
│   └── project-structure.md    # This file
│
├── data/                       # Created at runtime
│   └── knowledge.db            # Document metadata (SQLite)
│
└── uploads/                    # Created at runtime
    └── (uploaded files)
```

---

## How the pieces connect

### 1. User opens the app

```
Browser
  → app.py  (GET /)
  → templates/index.html
  → static/css/style.css
  → static/js/app.js
```

### 2. Upload a document

```
static/js/app.js
  → app.py  (POST /api/upload)
  → backend/services/upload.py
       ├── backend/config.py          (allowed types, paths)
       ├── backend/database.py        (save metadata)
       ├── backend/services/extract.py
       │     └── backend/prompts/vision.py  (if image / scanned PDF)
       └── backend/services/search.py (embed + Pinecone)
  → file saved in uploads/
  → row saved in data/knowledge.db
```

### 3. Ask a question

```
static/js/app.js
  (sends question + recent chat messages)
  → app.py  (POST /api/chat)
  → backend/services/conversation.py
       │
       ├── STAGE 1 — Orchestrator
       │     uses backend/prompts/chat.py
       │     decides: clarify | answer about app | search manuals
       │
       └── STAGE 2 — Grounded answer (only if search is needed)
             ├── backend/services/search.py   (Pinecone)
             └── backend/prompts/chat.py      (answer rules)
  → answer + sources back to the browser
```

### 4. List or delete documents

```
static/js/app.js
  → app.py  (GET /api/documents  or  DELETE /api/documents/<id>)
  → backend/database.py
  → backend/services/upload.py   (delete also clears Pinecone + disk file)
  → backend/services/search.py
```

---

## Quick file guide

| File | Job |
|---|---|
| `app.py` | Starts the server; defines all API routes |
| `backend/config.py` | API keys, model names, chunk size |
| `backend/database.py` | Document list in SQLite |
| `backend/services/upload.py` | Full upload pipeline |
| `backend/services/extract.py` | Text extraction + chunking |
| `backend/services/search.py` | Vector store (Pinecone) |
| `backend/services/conversation.py` | Chat logic (two stages) |
| `backend/prompts/chat.py` | Conversation / answer prompts |
| `backend/prompts/vision.py` | OCR-style vision prompt |
| `templates/index.html` | UI layout |
| `static/js/app.js` | Frontend behavior |
| `static/css/style.css` | Frontend look |

---

## Runtime folders

| Folder | Purpose |
|---|---|
| `data/` | SQLite database (`knowledge.db`) |
| `uploads/` | Original uploaded files |
| `.venv/` | Python virtual environment (local) |

These are created automatically when you run the app. Uploaded files and the database are gitignored.
