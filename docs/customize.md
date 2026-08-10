# Customize

## Change chat behavior

Edit `backend/prompts/chat.py`:

| Prompt | Purpose |
|---|---|
| `ORCHESTRATOR_SYSTEM_PROMPT` | When to clarify, retrieve, or answer about the app |
| `GROUNDED_SYSTEM_PROMPT` | How manual-based answers are written |
| `APP_HELP_SYSTEM_PROMPT` | How the assistant explains itself |
| `STEP_BY_STEP_ADDENDUM` | Extra rules when step-by-step mode is on |

## Change image / scan text extraction

Edit `backend/prompts/vision.py`.

## Change models or chunking

Edit `backend/config.py`:

```python
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
VISION_MODEL = "gpt-4.1-mini"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
MAX_HISTORY_MESSAGES = 12
```

If you change the embedding model, also update `EMBEDDING_DIMENSION`.

## Add a file type

1. Add the extension in `ALLOWED_EXTENSIONS` (`backend/config.py`)
2. Add a loader in `backend/services/extract.py`
3. Update the file picker `accept` list in `templates/index.html`

## Change branding

- Text: `templates/index.html`
- Colors / layout: `static/css/style.css`

## Reset knowledge

1. Delete files in `uploads/`
2. Delete `data/knowledge.db`
3. Delete vectors in Pinecone (or delete documents in the UI)

Restart the app to recreate the database.
