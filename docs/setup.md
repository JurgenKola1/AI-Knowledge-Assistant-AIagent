# Setup Guide

## Requirements

- Python 3.10 or newer
- OpenAI API key
- Pinecone API key (free tier works for testing)
- Internet connection (for OpenAI and Pinecone APIs)

## Step 1: Install dependencies

```bash
cd "AI Knowledge Assistant Agent"
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

## Step 2: Configure environment variables

Copy the example file:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and set your values:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | From [platform.openai.com](https://platform.openai.com) |
| `PINECONE_API_KEY` | Yes | From [pinecone.io](https://www.pinecone.io) |
| `PINECONE_INDEX_NAME` | No | Defaults to `knowledge-assistant-index` |
| `FLASK_SECRET_KEY` | No | Change in production |

**Important:** Never commit `.env` to git. Remove or replace real keys before sharing the project publicly.

## Step 3: Run the application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Step 4: First upload

1. Upload a test document (PDF or TXT works well)
2. Wait for status **Ready**
3. Ask a question related to the document content

On first upload, the app creates the Pinecone index automatically. This may take a few seconds.

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `Upload failed` | Missing or invalid API keys | Check `.env` values |
| Empty answers | No relevant chunks found | Upload more documents or rephrase question |
| Pinecone error | Index not ready | Wait a few seconds and retry |
| Port in use | Another app on port 5000 | Stop other process or change port in `app.py` |

## Folder creation

These folders are created automatically when the app runs:

- `data/` — SQLite database
- `uploads/` — uploaded files

Both are gitignored except for `.gitkeep` placeholder files.
