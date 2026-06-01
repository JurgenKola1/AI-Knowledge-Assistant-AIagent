"""Document upload pipeline: save file, extract text, chunk, embed, store."""

from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

from backend.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from backend.database import create_document, delete_document_record, update_document
from backend.services.document_loader import chunk_documents, load_document
from backend.services.vector_store import add_chunks, delete_document_vectors, ensure_index


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage) -> tuple[int, Path]:
    original_name = secure_filename(file_storage.filename or "upload")
    extension = original_name.rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid4().hex}.{extension}"
    stored_path = UPLOAD_DIR / stored_name
    file_storage.save(stored_path)

    doc_id = create_document(
        filename=original_name,
        stored_path=str(stored_path),
        file_type=extension,
    )
    return doc_id, stored_path


def process_document(doc_id: int, stored_path: Path, source_name: str) -> None:
    try:
        ensure_index()
        pages, page_count = load_document(stored_path, source_name=source_name)
        if not pages:
            update_document(
                doc_id,
                status="failed",
                error_message="No readable text could be extracted from this file.",
            )
            return

        chunks = chunk_documents(pages, document_id=doc_id)
        add_chunks(chunks)
        update_document(
            doc_id,
            status="ready",
            page_count=page_count,
            chunk_count=len(chunks),
        )
    except Exception as exc:
        update_document(
            doc_id,
            status="failed",
            error_message=str(exc),
        )
        raise


def remove_document(doc_id: int) -> bool:
    doc = delete_document_record(doc_id)
    if not doc:
        return False

    delete_document_vectors(doc_id)

    stored_path = Path(doc["stored_path"])
    if stored_path.exists():
        stored_path.unlink()
    return True
