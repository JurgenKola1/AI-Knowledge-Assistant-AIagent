"""
AI Knowledge Assistant Agent — Flask API entry point.

Routes handle document upload, listing, deletion, and chat Q&A.
"""

import traceback

from flask import Flask, jsonify, render_template, request

from backend.config import FLASK_SECRET_KEY
from backend.database import init_db, list_documents
from backend.services.conversation import answer_question
from backend.services.upload import allowed_file, process_document, remove_document, save_upload

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


@app.before_request
def setup():
    if not getattr(app, "_db_initialized", False):
        init_db()
        app._db_initialized = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/documents", methods=["GET"])
def api_list_documents():
    return jsonify({"documents": list_documents()})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file_storage = request.files["file"]
    if not file_storage.filename:
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file_storage.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    try:
        doc_id, stored_path = save_upload(file_storage)
        process_document(doc_id, stored_path, source_name=file_storage.filename)
        return jsonify({"message": "Document processed successfully.", "document_id": doc_id})
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Upload failed: {exc}"}), 500


@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
def api_delete_document(doc_id: int):
    if remove_document(doc_id):
        return jsonify({"message": "Document deleted."})
    return jsonify({"error": "Document not found."}), 404


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400

    document_id = data.get("document_id")
    if document_id is not None and document_id != "":
        try:
            document_id = int(document_id)
        except (TypeError, ValueError):
            return jsonify({"error": "document_id must be an integer."}), 400
    else:
        document_id = None

    step_by_step = bool(data.get("step_by_step", False))

    raw_messages = data.get("messages") or []
    if raw_messages and not isinstance(raw_messages, list):
        return jsonify({"error": "messages must be a list."}), 400

    conversation_state = data.get("conversation_state")
    if conversation_state is not None and not isinstance(conversation_state, dict):
        return jsonify({"error": "conversation_state must be an object."}), 400

    try:
        result = answer_question(
            question,
            document_id=document_id,
            step_by_step=step_by_step,
            messages=raw_messages,
            conversation_state=conversation_state,
        )
        return jsonify(result)
    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Chat failed: {exc}"}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
