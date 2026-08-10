# Setup

## Requirements

- Python 3.10+
- OpenAI API key
- Pinecone API key

## Install

```bash
cd "AI Knowledge Assistant Agent"
python -m venv .venv
```

Activate:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Configure

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | From platform.openai.com |
| `PINECONE_API_KEY` | Yes | From pinecone.io |
| `PINECONE_INDEX_NAME` | No | Default: `knowledge-assistant-index` |
| `FLASK_SECRET_KEY` | No | Change in production |

Never commit `.env`.

## Run

```bash
python app.py
```

Open http://localhost:5000

## First use

1. Upload a PDF or TXT manual
2. Wait for status **Ready**
3. Ask a question about that document

The Pinecone index is created automatically on first upload.

## Troubleshooting

| Problem | Fix |
|---|---|
| Upload failed | Check API keys in `.env` |
| Empty / not-found answers | Upload the right manual or rephrase |
| Port in use | Stop the other process on port 5000 |

`data/` and `uploads/` are created automatically at runtime.
