# AI Knowledge Assistant Agent

A document-based Q&A agent for business teams. Upload PDFs, Word files, and images, then ask questions answered only from your uploaded content.

Built as a teaching project for the book **Building Business AI Agents: A Technical Guide to Designing, Deploying, and Selling AI Automation Systems**.

## What it does

- Upload company documents through a simple web UI
- Extract text from PDFs, Word files, plain text, and images
- Store document chunks in a vector database for semantic search
- Answer questions using retrieved context and OpenAI
- Show source documents (filename and page) for each answer

## Main features

| Feature | Description |
|---|---|
| Document upload | Drag-and-drop or browse to upload files |
| Multi-format support | PDF, DOCX, TXT, MD, and common image formats |
| RAG chat | Answers grounded in uploaded documents only |
| Source citations | Hidden behind a menu in each answer |
| Document management | List and delete uploaded files |

## How it works

```
User Question → Frontend → Backend → Knowledge Search → Prompt Logic → AI Model → Final Answer
```

1. User uploads a document → text is extracted and split into chunks
2. Chunks are embedded and stored in Pinecone
3. User asks a question → similar chunks are retrieved
4. Retrieved text is added to a prompt → OpenAI generates the answer
5. Answer and sources are sent back to the browser

See [docs/how-it-works.md](docs/how-it-works.md) for a step-by-step walkthrough.

## Project structure

```
AI Knowledge Assistant Agent/
├── app.py                 # Flask API and web routes
├── backend/
│   ├── config.py          # Settings and environment variables
│   ├── database.py        # SQLite document metadata
│   └── services/
│       ├── document_loader.py   # Text extraction and chunking
│       ├── ingestion.py         # Upload pipeline
│       ├── rag.py               # Question answering
│       └── vector_store.py      # Pinecone search and storage
├── prompts/
│   ├── chat.py            # RAG system and user prompts
│   └── vision.py          # Image/scanned PDF extraction prompt
├── templates/             # HTML (frontend)
├── static/                # CSS and JavaScript (frontend)
├── data/                  # SQLite database (created at runtime)
├── uploads/               # Uploaded files (created at runtime)
└── docs/                  # Book documentation
```

## Setup

1. **Clone or download** the project

2. **Create a virtual environment and install dependencies**

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
copy .env.example .env        # Windows
```

Edit `.env` and add your API keys. See [docs/setup.md](docs/setup.md) for details.

4. **Run the app**

```bash
python app.py
```

5. **Open** [http://localhost:5000](http://localhost:5000)

The Pinecone index is created automatically on the first document upload.

## Example usage

1. Upload a PDF manual or policy document
2. Wait until the status shows **Ready**
3. Type a question such as: *"What are the steps to process a refund?"*
4. Read the answer and click **⋯** to view source documents

## API endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/api/documents` | List uploaded documents |
| POST | `/api/upload` | Upload and process a file |
| DELETE | `/api/documents/<id>` | Delete a document |
| POST | `/api/chat` | Ask a question (`{"question": "..."}`) |

## Documentation

| File | Contents |
|---|---|
| [docs/setup.md](docs/setup.md) | Installation and configuration |
| [docs/architecture.md](docs/architecture.md) | System design and data flow |
| [docs/how-it-works.md](docs/how-it-works.md) | Upload and chat pipeline |
| [docs/customization.md](docs/customization.md) | Change prompts, models, and behavior |
| [docs/tools-and-technologies.md](docs/tools-and-technologies.md) | Full stack reference |

## Environment variables

| Variable | What it is used for | Where it is used |
|---|---|---|
| `OPENAI_API_KEY` | Embeddings, chat, and vision text extraction | `backend/config.py` |
| `PINECONE_API_KEY` | Vector database access | `backend/config.py` |
| `PINECONE_INDEX_NAME` | Name of the Pinecone index | `backend/config.py`, `vector_store.py` |
| `FLASK_SECRET_KEY` | Flask session security | `app.py` |

Do not commit real API keys. Use `.env.example` as a template only.

## Supported file types

PDF, DOCX, DOC, TXT, MD, PNG, JPG, JPEG, WEBP, GIF, BMP, TIFF
