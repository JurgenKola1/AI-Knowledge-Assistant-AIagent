"""Two-stage conversational RAG: LLM orchestrator, then grounded retrieval."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config import CHAT_MODEL, MAX_HISTORY_MESSAGES, OPENAI_API_KEY, TOP_K
from backend.database import list_documents
from backend.prompts.chat import (
    APP_HELP_SYSTEM_PROMPT,
    APP_HELP_USER_PROMPT,
    GROUNDED_SYSTEM_PROMPT,
    GROUNDED_USER_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    ORCHESTRATOR_USER_PROMPT,
    STATE_EXTRACTION_SYSTEM_PROMPT,
    STATE_EXTRACTION_USER_PROMPT,
    STEP_BY_STEP_ADDENDUM,
)
from backend.services.search import search_relevant_chunks

VALID_ACTIONS = {"clarify", "retrieve", "answer_app_question", "respond"}
STATE_KEYS = ("topic", "user_goal", "key_details", "active_document")


def _get_llm(temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(model=CHAT_MODEL, openai_api_key=OPENAI_API_KEY, temperature=temperature)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "unknown", "n/a"}:
        return None
    return text


def _normalize_messages(messages: list[dict] | None) -> list[dict[str, str]]:
    if not messages:
        return []

    normalized: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = (item.get("role") or "").strip().lower()
        content = (item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content})

    if len(normalized) > MAX_HISTORY_MESSAGES:
        older = normalized[:-MAX_HISTORY_MESSAGES]
        recent = normalized[-MAX_HISTORY_MESSAGES:]
        preview = "; ".join(
            f"{item['role']}: {item['content'][:80]}" for item in older[-4:]
        )
        summary = {
            "role": "assistant",
            "content": f"(Earlier conversation summarized) {preview}",
        }
        return [summary, *recent]
    return normalized


def _format_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        return "(No previous messages.)"
    lines = []
    for item in messages:
        label = "User" if item["role"] == "user" else "Assistant"
        lines.append(f"{label}: {item['content']}")
    return "\n".join(lines)


def _ready_documents() -> list[dict]:
    return [doc for doc in list_documents() if doc.get("status") == "ready"]


def _format_document_catalog(documents: list[dict]) -> str:
    if not documents:
        return "(No ready documents uploaded.)"
    return "\n".join(f"- id={doc['id']}: {doc['filename']}" for doc in documents)


def _selected_document_label(documents: list[dict], document_id: int | None) -> str:
    if document_id is None:
        return "All documents"
    for doc in documents:
        if int(doc["id"]) == int(document_id):
            return f"id={doc['id']}: {doc['filename']}"
    return f"id={document_id} (selected, but not in ready list)"


def _empty_state() -> dict[str, Any]:
    return {key: None for key in STATE_KEYS}


def _normalize_prior_state(prior_state: dict | None) -> dict[str, Any]:
    state = _empty_state()
    if not isinstance(prior_state, dict):
        return state
    for key in STATE_KEYS:
        state[key] = _clean_text(prior_state.get(key))
    return state


def _merge_key_details(existing: str | None, incoming: str | None) -> str | None:
    existing = _clean_text(existing)
    incoming = _clean_text(incoming)
    if not existing:
        return incoming
    if not incoming:
        return existing
    if incoming.lower() in existing.lower():
        return existing
    if existing.lower() in incoming.lower():
        return incoming

    existing_parts = [part.strip() for part in re.split(r"[;|]", existing) if part.strip()]
    for part in re.split(r"[;|]", incoming):
        cleaned = part.strip()
        if cleaned and not any(cleaned.lower() == item.lower() for item in existing_parts):
            existing_parts.append(cleaned)
    return "; ".join(existing_parts) if existing_parts else None


def _merge_states(*states: dict[str, Any]) -> dict[str, Any]:
    """Merge conversation states left-to-right.

    Earlier values are durable: later sources only fill empty fields.
    key_details always accumulates unique phrases.
    """
    merged = _empty_state()
    for state in states:
        if not state:
            continue
        for key in STATE_KEYS:
            value = _clean_text(state.get(key))
            if key == "key_details":
                merged[key] = _merge_key_details(merged.get(key), value)
            elif value and not merged.get(key):
                merged[key] = value
    return merged


def _format_known_state(state: dict[str, Any]) -> str:
    return (
        f"- topic: {state.get('topic')}\n"
        f"- user_goal: {state.get('user_goal')}\n"
        f"- key_details: {state.get('key_details')}\n"
        f"- active_document: {state.get('active_document')}"
    )


def _conversation_state_from_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {key: decision.get(key) for key in STATE_KEYS}


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _coerce_document_id(value: Any, allowed_ids: set[int]) -> int | None:
    if value is None or value == "":
        return None
    try:
        doc_id = int(value)
    except (TypeError, ValueError):
        return None
    if allowed_ids and doc_id not in allowed_ids:
        return None
    return doc_id


def _match_documents_in_text(text: str, documents: list[dict]) -> list[str]:
    if not text or not documents:
        return []
    lowered = text.lower()
    matches: list[str] = []
    for doc in documents:
        filename = (doc.get("filename") or "").strip()
        if not filename:
            continue
        stem = Path(filename).stem
        candidates = {filename.lower(), stem.lower()}
        # Also try spaced/underscored variants of the stem.
        candidates.add(stem.replace("_", " ").lower())
        candidates.add(stem.replace("-", " ").lower())
        if any(candidate and candidate in lowered for candidate in candidates):
            matches.append(filename)
    return matches


def _heuristic_state_from_history(
    history: list[dict[str, str]],
    documents: list[dict],
) -> dict[str, Any]:
    """Rule-based seed from chat text and document names (no LLM)."""
    state = _empty_state()
    if not history:
        return state

    user_messages = [item["content"] for item in history if item["role"] == "user"]
    full_text = "\n".join(item["content"] for item in history)

    mentioned = _match_documents_in_text(full_text, documents)
    if mentioned:
        state["active_document"] = mentioned[-1]

    if user_messages:
        # Prefer an early substantive user message as topic seed.
        for message in user_messages:
            if len(message) >= 12:
                state["topic"] = message[:220]
                break
        if not state["topic"]:
            state["topic"] = user_messages[0][:220]

        goal_candidates = [
            message
            for message in user_messages
            if "?" in message
            or re.search(
                r"\b(how|what|where|when|why|which|can you|could you|explain|find|show|help)\b",
                message,
                flags=re.IGNORECASE,
            )
        ]
        if goal_candidates:
            state["user_goal"] = goal_candidates[-1][:220]

        detail_parts = []
        for message in user_messages[-4:]:
            cleaned = message.strip()
            if cleaned and cleaned not in detail_parts:
                detail_parts.append(cleaned[:160])
        if detail_parts:
            state["key_details"] = "; ".join(detail_parts)

    return state


def _llm_extract_state(
    history: list[dict[str, str]],
    documents: list[dict],
) -> dict[str, Any]:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", STATE_EXTRACTION_SYSTEM_PROMPT),
            ("human", STATE_EXTRACTION_USER_PROMPT),
        ]
    )
    llm = _get_llm().bind(response_format={"type": "json_object"})
    raw_text = (prompt | llm | StrOutputParser()).invoke(
        {
            "document_catalog": _format_document_catalog(documents),
            "history": _format_history(history),
        }
    )
    raw = _extract_json(raw_text)
    return {
        "topic": _clean_text(raw.get("topic")),
        "user_goal": _clean_text(raw.get("user_goal")),
        "key_details": _clean_text(raw.get("key_details")),
        "active_document": _clean_text(raw.get("active_document")),
    }


def _infer_state_from_history(
    history: list[dict[str, str]],
    documents: list[dict] | None = None,
    prior_state: dict | None = None,
) -> dict[str, Any]:
    """Extract and preserve useful conversation context across turns.

    Combines:
    1) client-provided prior state from the last turn
    2) heuristic cues from history / document names
    3) LLM extraction when there is history to summarize
    """
    documents = documents or []
    prior = _normalize_prior_state(prior_state)
    heuristic = _heuristic_state_from_history(history, documents)

    # Use an LLM rebuild only when history exists but durable prior state is empty
    # (e.g. first turns, or a client that did not send conversation_state).
    # When prior state is present, the orchestrator updates it in one call.
    extracted = _empty_state()
    prior_has_signal = any(prior.get(key) for key in STATE_KEYS)
    if history and not prior_has_signal:
        try:
            extracted = _llm_extract_state(history, documents)
        except Exception:
            extracted = _empty_state()
    elif prior_has_signal:
        # Avoid re-dumping raw user messages into already-curated details.
        heuristic = {**heuristic, "key_details": None}

    # Prior state is durable; heuristics/extraction only fill gaps (details accumulate).
    merged = _merge_states(prior, extracted, heuristic)
    merged["turns"] = len(history)
    return merged


def _fallback_decision(known_state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = _normalize_prior_state(known_state)
    return {
        "action": "clarify",
        **state,
        "document_id": None,
        "clarification_question": (
            "I want to make sure I help with the right thing. "
            "Are you asking about this AI assistant, or about something in your uploaded documents?"
        ),
        "response": None,
        "search_query": None,
    }


def _resolve_document_id_from_name(
    active_document: str | None,
    documents: list[dict],
) -> int | None:
    if not active_document or not documents:
        return None
    needle = active_document.lower().strip()
    for doc in documents:
        filename = (doc.get("filename") or "").strip()
        stem = Path(filename).stem.lower()
        if needle in {filename.lower(), stem} or needle in filename.lower() or stem in needle:
            return int(doc["id"])
    return None


def _validate_decision(
    raw: dict[str, Any],
    *,
    documents: list[dict],
    selected_document_id: int | None,
    known_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate structured orchestrator output and apply safe defaults. No keyword routing."""
    allowed_ids = {int(doc["id"]) for doc in documents}
    action = (_clean_text(raw.get("action")) or "clarify").lower()
    if action not in VALID_ACTIONS:
        action = "clarify"

    decision = {
        "action": action,
        "topic": _clean_text(raw.get("topic")),
        "user_goal": _clean_text(raw.get("user_goal")),
        "key_details": _clean_text(raw.get("key_details")),
        "active_document": _clean_text(raw.get("active_document")),
        "document_id": _coerce_document_id(raw.get("document_id"), allowed_ids),
        "clarification_question": _clean_text(raw.get("clarification_question")),
        "response": _clean_text(raw.get("response")),
        "search_query": _clean_text(raw.get("search_query")),
    }

    # Preserve known context if the model omitted a field this turn.
    known = _normalize_prior_state(known_state)
    for key in STATE_KEYS:
        if key == "key_details":
            decision[key] = _merge_key_details(known.get(key), decision.get(key))
        elif not decision.get(key) and known.get(key):
            decision[key] = known[key]

    # Manual dropdown always wins for retrieval targeting.
    if selected_document_id is not None:
        decision["document_id"] = selected_document_id
        filename = None
        for doc in documents:
            if int(doc["id"]) == int(selected_document_id):
                filename = doc.get("filename")
                break
        decision["active_document"] = filename or decision.get("active_document")
    else:
        # No UI selection: search across documents. Keep active_document as a soft
        # hint for search_query only — do not hard-filter on a guessed filename.
        decision["document_id"] = None
        if len(documents) == 1:
            decision["document_id"] = int(documents[0]["id"])
            decision["active_document"] = documents[0].get("filename") or decision.get(
                "active_document"
            )
        elif decision.get("active_document"):
            # Only accept a soft name that actually exists in the catalog.
            resolved = _resolve_document_id_from_name(
                decision["active_document"], documents
            )
            if resolved is None:
                decision["active_document"] = None

    if decision["action"] == "clarify" and not decision["clarification_question"]:
        decision["clarification_question"] = (
            "Could you share a bit more about what you're looking for in the uploaded documents?"
        )

    if decision["action"] == "respond" and not decision["response"]:
        decision["action"] = "clarify"
        decision["clarification_question"] = (
            decision["clarification_question"]
            or "Could you tell me a bit more about what you need?"
        )

    if decision["action"] == "retrieve" and not decision["search_query"]:
        parts = [
            decision.get("topic"),
            decision.get("user_goal"),
            decision.get("key_details"),
            decision.get("active_document"),
        ]
        decision["search_query"] = " ".join(part for part in parts if part) or None

    return decision


def run_orchestrator(
    question: str,
    history: list[dict[str, str]],
    documents: list[dict],
    selected_document_id: int | None,
    prior_state: dict | None = None,
) -> dict[str, Any]:
    """STAGE 1: LLM decides clarify / retrieve / app answer / respond."""
    known_state = _infer_state_from_history(
        history,
        documents=documents,
        prior_state=prior_state,
    )
    if selected_document_id is not None:
        for doc in documents:
            if int(doc["id"]) == int(selected_document_id):
                known_state["active_document"] = doc.get("filename") or known_state.get(
                    "active_document"
                )
                break

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ORCHESTRATOR_SYSTEM_PROMPT),
            ("human", ORCHESTRATOR_USER_PROMPT),
        ]
    )
    llm = _get_llm().bind(response_format={"type": "json_object"})

    try:
        raw_text = (prompt | llm | StrOutputParser()).invoke(
            {
                "document_catalog": _format_document_catalog(documents),
                "selected_document": _selected_document_label(documents, selected_document_id),
                "known_state": _format_known_state(known_state),
                "history": _format_history(history),
                "question": question,
            }
        )
        raw = _extract_json(raw_text)
    except Exception:
        raw = _fallback_decision(known_state)

    return _validate_decision(
        raw,
        documents=documents,
        selected_document_id=selected_document_id,
        known_state=known_state,
    )


def _generate_app_answer(question: str, history: list[dict[str, str]]) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", APP_HELP_SYSTEM_PROMPT),
            ("human", APP_HELP_USER_PROMPT),
        ]
    )
    return (prompt | _get_llm() | StrOutputParser()).invoke(
        {
            "history": _format_history(history),
            "question": question,
        }
    )


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


def _generate_grounded_answer(
    question: str,
    history: list[dict[str, str]],
    context: str,
    decision: dict[str, Any],
    step_by_step: bool,
) -> str:
    system_prompt = GROUNDED_SYSTEM_PROMPT
    if step_by_step:
        system_prompt = f"{GROUNDED_SYSTEM_PROMPT}\n{STEP_BY_STEP_ADDENDUM}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", GROUNDED_USER_PROMPT),
        ]
    )
    return (prompt | _get_llm() | StrOutputParser()).invoke(
        {
            "history": _format_history(history),
            "context": context,
            "question": question,
            "topic": decision.get("topic"),
            "user_goal": decision.get("user_goal"),
            "key_details": decision.get("key_details"),
            "active_document": decision.get("active_document"),
        }
    )


def _run_grounded_retrieval(
    question: str,
    history: list[dict[str, str]],
    documents: list[dict],
    decision: dict[str, Any],
    *,
    top_k: int,
    step_by_step: bool,
) -> dict:
    """STAGE 2: search documents and answer only from retrieved evidence."""
    conversation_state = _conversation_state_from_decision(decision)
    if not documents:
        return {
            "answer": (
                "I could not find that information in the uploaded documents. "
                "Please upload a document, or tell me which file I should use."
            ),
            "sources": [],
            "meta": {
                "action": "retrieve",
                "decision": decision,
                "conversation_state": conversation_state,
            },
        }

    search_query = decision.get("search_query") or question
    results = search_relevant_chunks(
        search_query,
        top_k=top_k,
        document_id=decision.get("document_id"),
    )
    if not results:
        return {
            "answer": (
                "I could not find that information in the uploaded documents. "
                "Could you share another detail—such as a section name, date, "
                "keyword, or which document I should focus on?"
            ),
            "sources": [],
            "meta": {
                "action": "retrieve",
                "decision": decision,
                "search_query": search_query,
                "conversation_state": conversation_state,
            },
        }

    retrieved = [doc for doc, _score in results]
    answer = _generate_grounded_answer(
        question=question,
        history=history,
        context=_format_context(retrieved),
        decision=decision,
        step_by_step=step_by_step,
    )
    return {
        "answer": answer,
        "sources": _format_sources(retrieved),
        "meta": {
            "action": "retrieve",
            "decision": decision,
            "search_query": search_query,
            "conversation_state": conversation_state,
        },
    }


def _with_state_meta(action: str, decision: dict[str, Any], **extra: Any) -> dict:
    return {
        "action": action,
        "decision": decision,
        "conversation_state": _conversation_state_from_decision(decision),
        **extra,
    }


def answer_question(
    question: str,
    top_k: int = TOP_K,
    document_id: int | None = None,
    step_by_step: bool = False,
    messages: list[dict] | None = None,
    conversation_state: dict | None = None,
) -> dict:
    """Two-stage chat: orchestrate the turn, then retrieve only when needed."""
    history = _normalize_messages(messages)
    documents = _ready_documents()

    decision = run_orchestrator(
        question=question,
        history=history,
        documents=documents,
        selected_document_id=document_id,
        prior_state=conversation_state,
    )

    if decision["action"] == "clarify":
        return {
            "answer": decision["clarification_question"],
            "sources": [],
            "meta": _with_state_meta("clarify", decision),
        }

    if decision["action"] == "respond":
        return {
            "answer": decision["response"],
            "sources": [],
            "meta": _with_state_meta("respond", decision),
        }

    if decision["action"] == "answer_app_question":
        return {
            "answer": _generate_app_answer(question, history),
            "sources": [],
            "meta": _with_state_meta("answer_app_question", decision),
        }

    return _run_grounded_retrieval(
        question=question,
        history=history,
        documents=documents,
        decision=decision,
        top_k=top_k,
        step_by_step=step_by_step,
    )
