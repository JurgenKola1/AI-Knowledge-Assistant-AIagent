# How It Works

## Upload flow

1. Browser sends a file to `POST /api/upload`
2. `backend/services/upload.py` saves it under `uploads/` and creates a SQLite row
3. `backend/services/extract.py` pulls text from PDF, DOCX, text, or images
4. Text is split into chunks
5. `backend/services/search.py` embeds chunks and stores them in Pinecone
6. Document status becomes `ready` (or `failed` if no text was found)

## Chat flow (two stages)

1. Browser sends the question plus recent chat messages to `POST /api/chat`
2. **Stage 1 — Orchestrator** (`conversation.py` + `backend/prompts/chat.py`)
   - Reads the message, history, selected document, and available manuals
   - Decides: clarify, answer about the app, or retrieve from manuals
3. **Stage 2 — Grounded answer** (only when retrieval is needed)
   - Searches Pinecone
   - Answers only from retrieved text
   - Returns filename, page, and snippet

Conversation memory stays in the browser session only.

## Where things live

| What | Where |
|---|---|
| API routes | `app.py` |
| Settings / API keys | `backend/config.py` |
| Document list (SQLite) | `backend/database.py`, `data/knowledge.db` |
| Upload pipeline | `backend/services/upload.py` |
| Text extraction | `backend/services/extract.py` |
| Vector search | `backend/services/search.py` |
| Chat / conversation | `backend/services/conversation.py` |
| Prompts | `backend/prompts/chat.py`, `backend/prompts/vision.py` |
| Web UI | `templates/index.html`, `static/` |
| Uploaded files | `uploads/` |
