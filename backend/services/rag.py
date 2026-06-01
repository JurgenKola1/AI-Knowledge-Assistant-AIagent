"""Retrieval-augmented generation: search chunks, build prompt, return answer."""

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import CHAT_MODEL, OPENAI_API_KEY, TOP_K
from backend.services.vector_store import search_relevant_chunks
from prompts.chat import SYSTEM_PROMPT, USER_PROMPT


def _format_context(documents: list[Document]) -> str:
    sections = []
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")
        page_label = f", page {page}" if page else ""
        sections.append(f"[Source: {source}{page_label}]\n{doc.page_content}")
    return "\n\n---\n\n".join(sections)


def _format_sources(documents: list[Document]) -> list[dict]:
    seen = set()
    sources = []
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "source": source,
                "page": page,
                "document_id": doc.metadata.get("document_id"),
                "snippet": doc.page_content[:300],
            }
        )
    return sources


def answer_question(question: str, top_k: int = TOP_K) -> dict:
    """Retrieve relevant chunks and generate a grounded answer."""
    results = search_relevant_chunks(question, top_k=top_k)
    if not results:
        return {
            "answer": "No documents have been uploaded yet, or nothing relevant was found.",
            "sources": [],
        }

    documents = [doc for doc, _score in results]
    context = _format_context(documents)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]
    )
    llm = ChatOpenAI(model=CHAT_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0)
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": _format_sources(documents),
    }
