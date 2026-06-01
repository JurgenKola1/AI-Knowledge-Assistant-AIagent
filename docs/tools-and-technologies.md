# Project Name: AI Knowledge Assistant Agent

## Tools and Technologies Used

| Name | Type | What It Is | What It Is Used For | How It Is Used In This Project | Files Used |
|---|---|---|---|---|---|
| Python | Language | General-purpose programming language | Backend logic, API, document processing | Runs the entire server-side application | All `.py` files |
| Flask | Web framework | Lightweight Python web framework | HTTP routes and serving the UI | Serves pages and REST API endpoints | `app.py` |
| HTML | Markup | Structure of web pages | Page layout | Defines upload panel and chat UI | `templates/index.html` |
| CSS | Styling | Styles web pages | Visual design and layout | Styles panels, chat bubbles, upload zone | `static/css/style.css` |
| JavaScript | Frontend language | Browser-side scripting | API calls and dynamic UI | Handles upload, chat, document list | `static/js/app.js` |
| SQLite | Database | Embedded relational database | Local metadata storage | Stores document filenames, paths, status, chunk counts | `backend/database.py`, `data/knowledge.db` |
| Pinecone | Vector database (cloud) | Managed vector search service | Semantic search over document chunks | Stores embeddings; retrieves similar chunks for questions | `backend/services/vector_store.py` |
| OpenAI API | External API | AI models for text, embeddings, and vision | Embeddings, chat answers, image text extraction | Powers RAG answers and document parsing | `vector_store.py`, `rag.py`, `document_loader.py` |
| LangChain | Python library | Framework for LLM applications | Connects embeddings, vector store, prompts, and chat model | RAG chain, document splitting, Pinecone integration | `rag.py`, `vector_store.py`, `document_loader.py` |
| langchain-openai | Python library | LangChain OpenAI integrations | OpenAI embeddings and chat via LangChain | `OpenAIEmbeddings`, `ChatOpenAI` | `vector_store.py`, `rag.py` |
| langchain-pinecone | Python library | LangChain Pinecone integration | Vector store wrapper for Pinecone | `PineconeVectorStore` for add/search | `vector_store.py` |
| langchain-text-splitters | Python library | Text chunking utilities | Split long documents into searchable pieces | `RecursiveCharacterTextSplitter` | `document_loader.py` |
| langchain-core | Python library | Core LangChain abstractions | Documents, prompts, output parsers | `Document`, `ChatPromptTemplate`, `StrOutputParser` | `rag.py`, `document_loader.py` |
| pinecone-client (pinecone) | Python SDK | Official Pinecone Python client | Index management and vector operations | Creates index, deletes vectors by document ID | `vector_store.py` |
| PyMuPDF (fitz) | Python library | PDF reading and rendering | Extract text from PDF pages | Primary PDF text extraction; renders pages for vision fallback | `document_loader.py` |
| python-docx | Python library | Read Microsoft Word files | Extract text from DOCX files | Reads paragraph text from Word uploads | `document_loader.py` |
| Pillow (PIL) | Python library | Image processing | Normalize image formats before vision API | Converts images to compatible formats | `document_loader.py` |
| Werkzeug | Python library | WSGI utilities (Flask dependency) | Secure file names on upload | `secure_filename()` sanitizes uploaded filenames | `ingestion.py` |
| python-dotenv | Python library | Load `.env` files | Environment variable management | Loads API keys from `.env` at startup | `backend/config.py` |
| OpenAI Python SDK | Python library | Official OpenAI client | Direct API calls | Vision API for images and scanned PDF pages | `document_loader.py` |
| Jinja2 | Template engine | Flask default templating | Render HTML with Flask | Renders `index.html` | `app.py`, `templates/` |
| JSON | Data format | Structured data exchange | API request/response bodies | Chat requests and responses | `app.py`, `static/js/app.js` |
| Environment variables | Configuration | Key-value runtime config | Secure API key storage | OpenAI, Pinecone, and Flask secrets | `.env`, `backend/config.py` |
| UUID | Python stdlib | Unique identifiers | Avoid filename collisions | Renames uploads to unique hex names | `ingestion.py` |
| Base64 | Encoding | Binary-to-text encoding | Send images to OpenAI vision API | Encodes image bytes for API payload | `document_loader.py` |

---

## Environment Variables

| Variable Name | What It Is Used For | Where It Is Used |
|---|---|---|
| `OPENAI_API_KEY` | Authenticates OpenAI API calls for embeddings, chat, and vision | `backend/config.py` → `vector_store.py`, `rag.py`, `document_loader.py` |
| `PINECONE_API_KEY` | Authenticates Pinecone vector database access | `backend/config.py` → `vector_store.py` |
| `PINECONE_INDEX_NAME` | Names the Pinecone index where document vectors are stored | `backend/config.py`, `vector_store.py` |
| `FLASK_SECRET_KEY` | Signs Flask session cookies | `backend/config.py` → `app.py` |

Do not include real API key values in documentation or version control.

---

## Model Configuration (in code, not env)

| Setting | Value | Purpose | File |
|---|---|---|---|
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Converts text chunks to vectors | `backend/config.py` |
| `CHAT_MODEL` | `gpt-4.1-mini` | Generates answers from retrieved context | `backend/config.py` |
| `VISION_MODEL` | `gpt-4.1-mini` | Extracts text from images and scanned PDFs | `backend/config.py` |
| `EMBEDDING_DIMENSION` | 1536 | Vector size for Pinecone index | `backend/config.py` |
| `CHUNK_SIZE` | 1000 | Characters per document chunk | `backend/config.py` |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks | `backend/config.py` |
| `TOP_K` | 5 | Chunks retrieved per question | `backend/config.py` |

---

## Short Project Flow

How the tools connect together:

1. **User uploads a document** → JavaScript sends file to Flask (`app.py`)
2. **Flask saves the file** → disk (`uploads/`) + SQLite metadata (`database.py`)
3. **Text is extracted** → PyMuPDF, python-docx, or OpenAI vision (`document_loader.py`)
4. **Text is chunked** → LangChain text splitter (`document_loader.py`)
5. **Chunks are embedded** → OpenAI embeddings API (`vector_store.py`)
6. **Vectors are stored** → Pinecone cloud index (`vector_store.py`)
7. **User asks a question** → JavaScript → Flask `/api/chat` (`app.py`)
8. **Question is embedded and searched** → Pinecone similarity search (`vector_store.py`)
9. **Context + prompt are built** → `prompts/chat.py` + `rag.py`
10. **OpenAI generates answer** → LangChain chat chain (`rag.py`)
11. **Answer returned to browser** → JSON → chat UI (`app.js`)

---

## Why these choices were made

| Choice | Reason |
|---|---|
| Flask | Simple to teach; minimal boilerplate for a book project |
| SQLite | No extra database setup for readers running locally |
| Pinecone | Managed vector search; no local vector DB setup |
| LangChain | Standard RAG patterns; reduces custom glue code |
| Separate `prompts/` folder | Readers can customize agent behavior in one obvious place |
| OpenAI vision fallback | Handles scanned PDFs and image uploads without OCR libraries |
