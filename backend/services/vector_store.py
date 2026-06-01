"""Pinecone vector store: embeddings, search, and document cleanup."""

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import time

from backend.config import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    TOP_K,
)

_index_ready = False


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )


def ensure_index() -> None:
    """Create the Pinecone index on first use if it does not exist."""
    global _index_ready
    if _index_ready:
        return

    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = {index.name for index in pc.list_indexes()}
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    while not pc.describe_index(PINECONE_INDEX_NAME).status.get("ready"):
        time.sleep(1)

    _index_ready = True


def get_vector_store() -> PineconeVectorStore:
    ensure_index()
    return PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=_get_embeddings(),
        pinecone_api_key=PINECONE_API_KEY,
    )


def add_chunks(chunks) -> None:
    if not chunks:
        return
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)


def delete_document_vectors(document_id: int) -> None:
    ensure_index()
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    index.delete(filter={"document_id": {"$eq": document_id}})


def search_relevant_chunks(query: str, top_k: int = TOP_K):
    """Return the most similar document chunks for a user question."""
    vector_store = get_vector_store()
    return vector_store.similarity_search_with_score(query, k=top_k)
