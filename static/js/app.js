/** Frontend: document upload, chat, and source popover UI. */

const uploadZone = document.getElementById("uploadZone");
const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");
const uploadStatus = document.getElementById("uploadStatus");
const documentList = document.getElementById("documentList");
const documentSelect = document.getElementById("documentSelect");
const stepByStepToggle = document.getElementById("stepByStepToggle");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const chatWindow = document.getElementById("chatWindow");
const sendBtn = document.getElementById("sendBtn");
const libraryToggle = document.getElementById("libraryToggle");
const libraryCount = document.getElementById("libraryCount");
const libraryPanel = document.querySelector(".library");

/** Recent chat turns for this browser session only (not persisted). */
const conversationHistory = [];
const MAX_CLIENT_HISTORY = 12;

/** Durable context from the last orchestrator turn (topic, goal, details, document). */
let conversationState = null;

function setStatus(message, type = "info") {
  uploadStatus.hidden = false;
  uploadStatus.textContent = message;
  uploadStatus.className = `status-message ${type}`;
}

function clearStatus() {
  uploadStatus.hidden = true;
  uploadStatus.textContent = "";
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderDocumentSelect(documents) {
  const previous = documentSelect.value;
  const readyDocs = documents.filter((doc) => doc.status === "ready");

  documentSelect.innerHTML = '<option value="">All documents</option>';
  readyDocs.forEach((doc) => {
    const option = document.createElement("option");
    option.value = String(doc.id);
    option.textContent = doc.filename;
    documentSelect.appendChild(option);
  });

  if (previous && [...documentSelect.options].some((opt) => opt.value === previous)) {
    documentSelect.value = previous;
  } else {
    documentSelect.value = "";
  }
}

function renderDocuments(documents) {
  renderDocumentSelect(documents);
  libraryCount.textContent = String(documents.length);

  if (!documents.length) {
    documentList.innerHTML = '<li class="empty-state">No documents uploaded yet.</li>';
    return;
  }

  documentList.innerHTML = documents
    .map(
      (doc) => `
        <li class="document-item">
          <div class="document-meta">
            <p class="document-name">${escapeHtml(doc.filename)}</p>
            <p class="document-details">
              <span class="status-badge ${doc.status}">${doc.status}</span>
              · ${doc.file_type.toUpperCase()}
              · ${doc.page_count || 0} pages
            </p>
            ${
              doc.error_message
                ? `<p class="document-details" style="color:#dc2626;">${escapeHtml(doc.error_message)}</p>`
                : ""
            }
          </div>
          <button class="btn danger" data-delete-id="${doc.id}">Delete</button>
        </li>
      `
    )
    .join("");
}

async function loadDocuments() {
  const response = await fetch("/api/documents");
  const data = await response.json();
  renderDocuments(data.documents || []);
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  setStatus(`Uploading ${file.name}...`, "info");

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  await loadDocuments();

  if (!response.ok) {
    setStatus(data.error || "Upload failed.", "error");
    return;
  }

  setStatus(`${file.name} processed successfully.`, "success");
  setTimeout(clearStatus, 2500);
}

function appendMessage(role, content, sources = []) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const textNode = document.createElement("div");
  textNode.className = "bubble-text";
  textNode.textContent = content;
  bubble.appendChild(textNode);

  if (sources.length) {
    const sourcesWrap = document.createElement("div");
    sourcesWrap.className = "sources-wrap";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sources-toggle";
    toggle.title = "View sources";
    toggle.setAttribute("aria-label", "View sources");
    toggle.textContent = "⋯";

    const popover = document.createElement("div");
    popover.className = "sources-popover";
    popover.hidden = true;

    const heading = document.createElement("p");
    heading.className = "sources-heading";
    heading.textContent = "Sources";
    popover.appendChild(heading);

    const list = document.createElement("ul");
    sources.forEach((source) => {
      const item = document.createElement("li");

      const title = document.createElement("div");
      title.className = "source-title";
      const page = source.page ? `, page ${source.page}` : "";
      title.textContent = `${source.source}${page}`;
      item.appendChild(title);

      if (source.snippet) {
        const snippet = document.createElement("div");
        snippet.className = "source-snippet";
        snippet.textContent = source.snippet;
        item.appendChild(snippet);
      }

      list.appendChild(item);
    });
    popover.appendChild(list);

    popover.addEventListener("click", (event) => event.stopPropagation());

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      const isOpen = !popover.hidden;
      closeAllSourcePopovers();
      if (!isOpen) {
        popover.hidden = false;
        toggle.classList.add("active");
      }
    });

    sourcesWrap.appendChild(toggle);
    sourcesWrap.appendChild(popover);
    bubble.appendChild(sourcesWrap);
  }

  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function closeAllSourcePopovers() {
  chatWindow.querySelectorAll(".sources-popover").forEach((popover) => {
    popover.hidden = true;
  });
  chatWindow.querySelectorAll(".sources-toggle.active").forEach((btn) => {
    btn.classList.remove("active");
  });
}

document.addEventListener("click", closeAllSourcePopovers);

libraryToggle.addEventListener("click", () => {
  const collapsed = libraryPanel.classList.toggle("collapsed");
  libraryToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
});

// On narrow screens, start with the library collapsed so chat has more room.
if (window.matchMedia("(max-width: 1024px)").matches) {
  libraryPanel.classList.add("collapsed");
  libraryToggle.setAttribute("aria-expanded", "false");
}

browseBtn.addEventListener("click", () => fileInput.click());
uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadZone.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  if (file) uploadFile(file);
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) uploadFile(file);
  fileInput.value = "";
});

documentList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-delete-id]");
  if (!button) return;

  const docId = button.dataset.deleteId;
  if (!confirm("Delete this document from the knowledge base?")) return;

  const response = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
  if (response.ok) {
    await loadDocuments();
  } else {
    const data = await response.json();
    setStatus(data.error || "Delete failed.", "error");
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  const selectedDocumentId = documentSelect.value;
  const payload = {
    question,
    step_by_step: stepByStepToggle.checked,
    messages: conversationHistory.slice(-MAX_CLIENT_HISTORY),
  };
  if (selectedDocumentId) {
    payload.document_id = Number(selectedDocumentId);
  }
  if (conversationState && typeof conversationState === "object") {
    payload.conversation_state = conversationState;
  }

  appendMessage("user", question);
  questionInput.value = "";
  sendBtn.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      appendMessage("assistant", data.error || "Something went wrong.");
      return;
    }

    const answer = data.answer || "";
    appendMessage("assistant", answer, data.sources || []);
    conversationHistory.push({ role: "user", content: question });
    conversationHistory.push({ role: "assistant", content: answer });
    if (conversationHistory.length > MAX_CLIENT_HISTORY) {
      conversationHistory.splice(0, conversationHistory.length - MAX_CLIENT_HISTORY);
    }

    const nextState = data.meta && data.meta.conversation_state;
    if (nextState && typeof nextState === "object") {
      conversationState = nextState;
    }
  } catch (error) {
    appendMessage("assistant", "Could not reach the server.");
  } finally {
    sendBtn.disabled = false;
  }
});

// Enter sends the message; Shift+Enter adds a new line.
questionInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) return;
  event.preventDefault();
  if (sendBtn.disabled) return;
  chatForm.requestSubmit();
});

// On phones, keep the input visible when the keyboard opens
if (window.matchMedia("(max-width: 640px)").matches) {
  questionInput.addEventListener("focus", () => {
    setTimeout(() => {
      chatForm.scrollIntoView({ block: "end", behavior: "smooth" });
    }, 300);
  });
}

loadDocuments();
