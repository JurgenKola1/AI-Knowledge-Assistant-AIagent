# How It Works

This page explains the two main workflows: **uploading documents** and **asking questions**.

## Short project flow

User asks a question → frontend sends it to the backend → backend searches the knowledge base → relevant information is added to the AI prompt → OpenAI API generates an answer → backend sends the answer back to the frontend.

---

## Document upload pipeline

### 1. User selects a file

The browser sends the file to `POST /api/upload` via `static/js/app.js`.

### 2. File is saved

`backend/services/ingestion.py`:
- Validates the file extension
- Saves the file to `uploads/` with a unique name
- Creates a row in SQLite (`data/knowledge.db`) with status `processing`

### 3. Text is extracted

`backend/services/document_loader.py` reads the file based on type:

| File type | Method |
|---|---|
| PDF | PyMuPDF text extraction; vision API fallback for scanned pages |
| DOCX | python-docx paragraph extraction |
| TXT / MD | Direct file read |
| Images | OpenAI vision API with prompt from `prompts/vision.py` |

### 4. Text is chunked

LangChain's `RecursiveCharacterTextSplitter` splits text into overlapping chunks (default: 1000 characters, 200 overlap). Each chunk gets metadata: `document_id`, `source`, `page`, `chunk_index`.

### 5. Embeddings are stored

`backend/services/vector_store.py`:
- Sends chunks to OpenAI `text-embedding-3-small`
- Stores vectors in Pinecone with metadata
- Updates SQLite status to `ready`

---

## Question answering pipeline

### 1. User submits a question

JavaScript sends `POST /api/chat` with JSON: `{"question": "..."}`.

### 2. Similar chunks are retrieved

`backend/services/rag.py` calls `search_relevant_chunks()` in `vector_store.py`. Pinecone returns the top 5 most similar chunks (configurable via `TOP_K` in `config.py`).

### 3. Prompt is built

Retrieved chunks are formatted as context text. The prompt uses:
- **System prompt** from `prompts/chat.py` — tells the model to answer only from context
- **User prompt** from `prompts/chat.py` — includes context + question

### 4. OpenAI generates the answer

LangChain sends the prompt to `gpt-4.1-mini` with temperature 0 (consistent, factual answers).

### 5. Response is returned

The API returns:

```json
{
  "answer": "...",
  "sources": [
    {"source": "manual.pdf", "page": 3, "snippet": "..."}
  ]
}
```

The frontend displays the answer and hides sources behind a **⋯** menu.

---

## Where things live

| What | Where |
|---|---|
| Uploaded files | `uploads/` |
| Document list / status | `data/knowledge.db` |
| Searchable knowledge | Pinecone index |
| Chat prompts | `prompts/chat.py` |
| Vision prompt | `prompts/vision.py` |
| API routes | `app.py` |
| Search logic | `backend/services/vector_store.py` |
| Answer logic | `backend/services/rag.py` |
| Frontend UI | `templates/index.html`, `static/` |
