# Customization Guide

Common changes readers may want to make when adapting this agent for their own business.

## Change the agent personality

Edit `prompts/chat.py`:

- `SYSTEM_PROMPT` — controls tone, rules, and answer style
- `USER_PROMPT` — controls how context and questions are formatted

Example: add industry-specific rules, change the "not found" message, or require bullet-point answers.

## Change the vision extraction prompt

Edit `prompts/vision.py` if you need different text extraction behavior for images or scanned PDFs.

## Change AI models

Edit `backend/config.py`:

```python
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
VISION_MODEL = "gpt-4.1-mini"
```

If you change the embedding model, update `EMBEDDING_DIMENSION` to match (1536 for `text-embedding-3-small`).

## Change chunk size and retrieval

In `backend/config.py`:

| Setting | Default | Effect |
|---|---|---|
| `CHUNK_SIZE` | 1000 | Larger chunks = more context per piece |
| `CHUNK_OVERLAP` | 200 | Overlap helps avoid cutting sentences |
| `TOP_K` | 5 | Number of chunks sent to the model |

## Add supported file types

1. Add extension to `ALLOWED_EXTENSIONS` in `backend/config.py`
2. Add a loader function in `backend/services/document_loader.py`
3. Update the `accept` attribute in `templates/index.html`

## Change branding

Edit `templates/index.html` for title and header text.  
Edit `static/css/style.css` for colors and layout.

## Change vector database region

In `backend/services/vector_store.py`, the Pinecone index is created with:

```python
ServerlessSpec(cloud="aws", region="us-east-1")
```

Change the region if needed for latency or compliance.

## Reset the knowledge base

1. Delete files in `uploads/`
2. Delete `data/knowledge.db`
3. Delete vectors in Pinecone (via Pinecone console or delete documents through the UI)

Restart the app to recreate the SQLite database.

## Production considerations

Before deploying for real clients:

- Set a strong `FLASK_SECRET_KEY`
- Turn off `debug=True` in `app.py`
- Use a production WSGI server (e.g. Gunicorn)
- Add authentication if documents are sensitive
- Monitor OpenAI and Pinecone usage and costs
