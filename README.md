# AI Knowledge Assistant

Upload technical manuals and ask questions. Answers come from your documents, with source filename, page, and snippet.

## Features

- Upload PDF, DOCX, text, and images
- Conversational chat with session memory (browser only)
- Clarifies vague questions before searching manuals
- Document filter + step-by-step answer option
- Source citations with text snippets

## Project structure

```
AI Knowledge Assistant Agent/
├── app.py                 # Flask routes (upload, chat, UI)
├── LumaMark_LX500_Test_Manual.pdf  # Sample test manual (fictional)
├── backend/
│   ├── config.py          # Settings and API keys
│   ├── database.py        # SQLite document list
│   ├── prompts/
│   │   ├── chat.py        # Orchestrator and answer prompts
│   │   └── vision.py      # Image / scan text prompt
│   └── services/
│       ├── upload.py      # Save and process uploads
│       ├── extract.py     # Pull text from files
│       ├── search.py      # Pinecone embed / search
│       └── conversation.py# Chat orchestrator + answers
├── templates/             # HTML page
├── static/                # CSS and JavaScript
├── docs/                  # Setup and guides
├── data/                  # SQLite DB (runtime)
└── uploads/               # Uploaded files (runtime)
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add your OpenAI and Pinecone keys to `.env`, then:

```bash
python app.py
```

Open http://localhost:5000

More detail: [docs/setup.md](docs/setup.md)

## How chat works

1. **Orchestrator** decides: clarify, explain the app, or search manuals
2. **Retrieval** runs only when needed, then answers from document text only

See [docs/how-it-works.md](docs/how-it-works.md).

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/documents` | List documents |
| POST | `/api/upload` | Upload a file |
| DELETE | `/api/documents/<id>` | Delete a document |
| POST | `/api/chat` | Ask a question |

Chat body example:

```json
{
  "question": "What should I check if the LumaMark LX-500 shows alarm E305?",
  "messages": [],
  "document_id": null,
  "step_by_step": false
}
```

## Docs

| File | Contents |
|---|---|
| [docs/setup.md](docs/setup.md) | Install and run |
| [docs/how-it-works.md](docs/how-it-works.md) | Upload and chat flow |
| [docs/customize.md](docs/customize.md) | Prompts, models, branding |
| [docs/project-structure.md](docs/project-structure.md) | Folder map and connections |

## Environment variables

| Variable | Used for |
|---|---|
| `OPENAI_API_KEY` | Chat, embeddings, vision OCR |
| `PINECONE_API_KEY` | Vector search |
| `PINECONE_INDEX_NAME` | Pinecone index name (optional) |
| `FLASK_SECRET_KEY` | Flask secret (change in production) |

Do not commit real keys. Use `.env.example` as a template.
