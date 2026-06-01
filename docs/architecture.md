# Architecture

## Overview

The AI Knowledge Assistant Agent is a **Retrieval-Augmented Generation (RAG)** application. It combines document search with an AI language model so answers come from uploaded files, not from general model knowledge.

## High-level flow

```
User Question
    ↓
Frontend (HTML / CSS / JavaScript)
    ↓
Backend (Flask API)
    ↓
Knowledge Search / Retrieval (Pinecone)
    ↓
Prompt Logic (prompts/ + rag.py)
    ↓
AI Model (OpenAI)
    ↓
Final Answer (+ sources)
```

## Upload flow

```
User uploads file
    ↓
Flask saves file to uploads/
    ↓
SQLite records document metadata
    ↓
document_loader.py extracts text
    ↓
Text split into chunks
    ↓
OpenAI creates embeddings
    ↓
Chunks stored in Pinecone with metadata
```

## Chat flow

```
User types question
    ↓
JavaScript sends POST /api/chat
    ↓
rag.py searches Pinecone for similar chunks
    ↓
Retrieved text inserted into prompt
    ↓
OpenAI generates answer
    ↓
JSON response returned to frontend
```

## Components

| Layer | Location | Role |
|---|---|---|
| Frontend | `templates/`, `static/` | Upload UI, chat UI, API calls |
| API | `app.py` | HTTP routes and request handling |
| Config | `backend/config.py` | Paths, models, API keys |
| Metadata DB | `backend/database.py`, `data/knowledge.db` | Document registry |
| Ingestion | `backend/services/ingestion.py` | Upload pipeline |
| Text extraction | `backend/services/document_loader.py` | Read PDF, Word, images |
| Vector store | `backend/services/vector_store.py` | Pinecone embed/search |
| RAG | `backend/services/rag.py` | Retrieve + generate answer |
| Prompts | `prompts/` | System and user prompt templates |

## Data storage

| Data | Location | Purpose |
|---|---|---|
| Original files | `uploads/` | Saved uploads on disk |
| Document metadata | `data/knowledge.db` | Filenames, status, chunk counts |
| Vector embeddings | Pinecone (cloud) | Semantic search over chunks |

## Important files

| File | Purpose |
|---|---|
| `app.py` | Entry point and REST API |
| `backend/config.py` | All configuration |
| `backend/database.py` | SQLite CRUD for documents |
| `backend/services/ingestion.py` | Upload → chunk → embed pipeline |
| `backend/services/document_loader.py` | File parsing and chunking |
| `backend/services/vector_store.py` | Pinecone operations |
| `backend/services/rag.py` | Question answering logic |
| `prompts/chat.py` | Chat system and user prompts |
| `prompts/vision.py` | Vision extraction prompt |
| `static/js/app.js` | Frontend API and chat logic |
| `templates/index.html` | Page layout |

## Design choices

- **SQLite** for metadata — simple, local, no extra setup for readers
- **Pinecone** for vectors — managed vector DB, easy to scale in production
- **LangChain** — connects embeddings, vector store, and chat model with less boilerplate
- **Separate prompts folder** — easy to customize agent behavior without touching core logic
