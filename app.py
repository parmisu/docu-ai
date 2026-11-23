from __future__ import annotations

import hashlib
import html
from io import BytesIO
from pathlib import Path
import re
import time

import streamlit as st
from pypdf import PdfReader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ollama_error_handling import invoke_ollama_safely
from query_intent import retrieve_context
from pdf_validation import has_pdf_signature
from text_cleaning import clean_extracted_text
from ui_theme import (
    ICON_FILE,
    ICON_LOCK,
    LOGO_SVG,
    apply_docu_theme,
    image_data_uri,
)


BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "docs" / "docu_ai_logo.png"

MODEL_NAME = "llama3.2:3b"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
RELEVANCE_THRESHOLD = 0.15
MAX_UPLOAD_MB = 50


st.set_page_config(
    page_title="DocuAI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_docu_theme()


# ==================================================
# RAG RESOURCES
# ==================================================

@st.cache_resource
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


@st.cache_resource
def get_vector_store(
    document_key: str,
    _documents: list[Document],
) -> Chroma:
    return Chroma.from_documents(
        documents=_documents,
        embedding=get_embeddings(),
    )


# ==================================================
# SESSION STATE
# ==================================================

def init_state() -> None:
    defaults = {
        # Documents uploaded in this session, in upload order:
        # [{"key", "name", "bytes"}]
        "documents": [],
        "current_doc_key": None,
        "messages": [],
        "preview_page": 1,
        "source_pages": [],
        "uploader_nonce": 0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.source_pages = []
    st.session_state.preview_page = 1


def ask(
    question: str,
) -> None:
    """Queue a question; the next run answers it in the chat pane."""

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "time": time.time(),
        }
    )
    st.rerun()


def find_document(
    document_key: str | None,
) -> dict | None:
    for document in st.session_state.documents:
        if document["key"] == document_key:
            return document
    return None


def open_document(
    name: str,
    data: bytes,
) -> None:
    """Add a document to the session (deduplicated) and make it current."""

    document_key = hashlib.sha256(data).hexdigest()

    if find_document(document_key) is None:
        st.session_state.documents.append(
            {
                "key": document_key,
                "name": name,
                "bytes": data,
            }
        )

    if st.session_state.current_doc_key != document_key:
        st.session_state.current_doc_key = document_key
        reset_chat()


# ==================================================
# LOGO
# ==================================================

def logo_markup() -> str:
    logo_uri = image_data_uri(LOGO_PATH)

    if logo_uri:
        # st.html strips <img>, so the logo is drawn as a background.
        visual = (
            '<span class="docu-brand-logo" '
            f'style="background-image:url(\'{logo_uri}\')"></span>'
        )
    else:
        visual = LOGO_SVG

    return (
        '<div class="docu-brand">'
        f'{visual}'
        '<div class="docu-brand-name">DocuAI</div>'
        '</div>'
    )


# ==================================================
# SIDEBAR
# ==================================================

def render_sidebar() -> None:

    with st.sidebar:

        st.html(logo_markup())

        if st.button(
            "New chat",
            key="new_chat",
            icon=":material/add:",
            width="stretch",
        ):
            st.session_state.current_doc_key = None
            reset_chat()
            st.rerun()

        st.html(
            '<div class="sidebar-section-label">Your documents</div>'
        )

        with st.container(key="sidebar_docs"):

            if not st.session_state.documents:
                st.html(
                    '<div class="sidebar-empty">'
                    'Documents you upload will appear here.'
                    '</div>'
                )

            for document in st.session_state.documents:

                is_active = (
                    document["key"]
                    == st.session_state.current_doc_key
                )

                prefix = "doc_active_" if is_active else "doc_"

                if st.button(
                    document["name"],
                    key=f"{prefix}{document['key'][:16]}",
                    icon=":material/draft:",
                    width="stretch",
                    help=document["name"],
                ) and not is_active:
                    st.session_state.current_doc_key = document["key"]
                    reset_chat()
                    st.rerun()

        st.html(
            '<div class="sidebar-footer">'
            '<div class="sidebar-avatar"></div>'
            '<div>'
            '<div class="sidebar-footer-title">Your workspace</div>'
            '<div class="sidebar-footer-meta">Local · Private</div>'
            '</div>'
            '</div>'
        )


# ==================================================
# QUESTION VALIDATION
# ==================================================

def validate_question(
    question: str,
) -> str | None:

    if len(question) < 3:
        return (
            "Please enter a longer question."
        )

    if not re.search(
        r"[A-Za-z0-9]",
        question,
    ):
        return (
            "Please enter a question using words, "
            "not only emojis or symbols."
        )

    if len(question) > 500:
        return (
            "Your question is too long. "
            "Please keep it under 500 characters."
        )

    return None


# ==================================================
# PDF READING
# ==================================================

def read_pdf(
    uploaded_bytes: bytes,
    source_name: str,
):

    buffer = BytesIO(
        uploaded_bytes
    )

    if not has_pdf_signature(
        buffer
    ):
        raise ValueError(
            "The uploaded file is not a valid PDF. "
            "Please upload a genuine PDF document."
        )

    try:
        reader = PdfReader(
            BytesIO(
                uploaded_bytes
            )
        )

    except Exception as exc:

        raise ValueError(
            "This PDF could not be opened. "
            "The file may be corrupted, incomplete, "
            "or not a valid PDF."
        ) from exc

    page_documents: list[Document] = []
    page_texts: list[str] = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:

            cleaned = (
                clean_extracted_text(
                    page.extract_text()
                    or ""
                )
            )

        except Exception as exc:

            raise ValueError(
                "The PDF could not be read correctly. "
                "One or more pages may be corrupted "
                "or incomplete."
            ) from exc

        page_texts.append(
            cleaned
        )

        if cleaned:

            page_documents.append(
                Document(
                    page_content=cleaned,
                    metadata={
                        "source": source_name,
                        "page": page_number,
                    },
                )
            )

    if not page_documents:

        raise ValueError(
            "No extractable text was found in this PDF. "
            "The document may be empty, scanned, "
            "or image-only. OCR is not currently supported."
        )

    return (
        reader,
        page_documents,
        page_texts,
    )


# ==================================================
# CHUNKING
# ==================================================

def build_chunks(
    page_documents: list[Document],
) -> list[Document]:

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
    )

    return splitter.split_documents(
        page_documents
    )


# ==================================================
# PROMPT
# ==================================================

OVERVIEW_INSTRUCTIONS = """
The user is asking about the document as a whole (for example a summary,
its main points or what it is about). The context below is a set of
excerpts sampled from across the whole document, in reading order.
- Start with one or two sentences describing what the document is about.
- Then list its main points as a short numbered list.
- Cover the whole document, not only the first excerpt.
- Only describe what the excerpts actually say.
"""

def build_prompt(
    question: str,
    results: list[Document],
    overview: bool = False,
) -> str:

    context = "\n\n".join(
        (
            f"[Page "
            f"{item.metadata.get('page', 'Unknown')}"
            f"]\n"
            f"{item.page_content}"
        )
        for item in results
    )

    return f"""
You are DocuAI, a local document question-answering assistant.

Answer the user's question using ONLY the supplied document context.
{OVERVIEW_INSTRUCTIONS if overview else ""}
Rules:
- Be direct, concise, and useful.
- Use all relevant information from the context.
- Preserve numbered lists and structure when the document uses them.
- Never invent facts that are not supported by the context.
- If the answer cannot be supported by the context, say exactly:
  "I could not find the answer in the uploaded document."

Context:
{context}

Question:
{question}

Answer:
""".strip()


# ==================================================
# SOURCES
# ==================================================

def unique_sources(
    results: list[Document],
    limit: int = 3,
) -> list[Document]:

    seen: set[
        tuple[str, object]
    ] = set()

    sources: list[
        Document
    ] = []

    for item in results:

        key = (
            str(
                item.metadata.get(
                    "source",
                    "Unknown document",
                )
            ),
            item.metadata.get(
                "page",
                "Unknown page",
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        sources.append(
            item
        )

        if len(sources) >= limit:
            break

    return sources


# ==================================================
# TEXT UTIL
# ==================================================

def truncate(
    text: str,
    limit: int,
) -> str:

    compact = " ".join(
        text.split()
    )

    if len(compact) <= limit:
        return compact

    return (
        compact[
            : limit - 1
        ].rstrip()
        + "…"
    )




def first_sentence(
    text: str,
    limit: int = 300,
) -> str:
    """First sentence of a chunk, whitespace-collapsed."""

    compact = " ".join(text.split())

    match = re.match(r"(.+?[.!?])(?=\s|$)", compact)

    sentence = match.group(1) if match else compact

    return sentence[:limit]


_STOPWORDS = {
    "the", "and", "for", "are", "was", "were", "this", "that", "with",
    "from", "what", "which", "how", "why", "who", "when", "where", "does",
    "have", "has", "into", "our", "their", "your", "you", "can", "will",
    "about", "should", "would", "could", "there", "these", "those",
}


def _terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 2 and word not in _STOPWORDS
    }


def split_headings(
    text: str,
) -> list[str]:
    """
    Split extracted text into segments so headings ("04 Pricing", short
    lines without end punctuation) are not glued onto the next sentence.
    """

    segments: list[str] = []
    current: list[str] = []
    lines = [line.strip() for line in text.split("\n")]

    for index, line in enumerate(lines):

        if not line:
            if current:
                segments.append(" ".join(current))
                current = []
            continue

        current.append(line)

        next_line = next(
            (candidate for candidate in lines[index + 1:] if candidate),
            "",
        )

        is_heading = (
            len(line) <= 60
            and not re.search(r"[.!?:,;]$", line)
            and next_line[:1].isupper()
        )

        if is_heading:
            segments.append(" ".join(current))
            current = []

    if current:
        segments.append(" ".join(current))

    return segments


def key_passage(
    chunk_text: str,
    reference: str,
    limit: int = 300,
) -> str:
    """
    The sentence of a retrieved chunk that best overlaps the question and
    answer. Used for the source-card snippet and the preview highlight.
    """

    compact = " ".join(chunk_text.split())
    sentences = [
        " ".join(sentence.split())
        for segment in split_headings(chunk_text)
        for sentence in re.split(r"(?<=[.!?])\s+", segment)
        if sentence.strip()
    ]

    if not sentences:
        return compact[:limit]

    wanted = _terms(reference)

    def score(sentence: str) -> float:
        terms = _terms(sentence)
        if not terms:
            return 0.0
        return len(terms & wanted) / len(terms) ** 0.5

    best = max(sentences, key=score)

    return (best if score(best) > 0 else sentences[0])[:limit]


def source_passage(
    source: dict,
) -> str:
    return source.get("passage") or first_sentence(source.get("text", ""))


def relative_time(
    timestamp: float | None,
) -> str:
    if not timestamp or time.time() - timestamp < 60:
        return "Just now"

    return time.strftime("%H:%M", time.localtime(timestamp))


# ==================================================
# PDF LOADING (cached per document)
# ==================================================

@st.cache_data(show_spinner=False, max_entries=20)
def load_pdf(
    document_key: str,
    _data: bytes,
    source_name: str,
) -> tuple[int, list[Document], list[str]]:

    reader, page_documents, page_texts = read_pdf(
        _data,
        source_name,
    )

    return len(reader.pages), page_documents, page_texts


# ==================================================
# EMPTY / UPLOAD STATE
# ==================================================

# Shown as hints on the upload screen and as one-click questions in a new
# chat. All three are document-level requests, which always get an answer.
SUGGESTED_QUESTIONS = (
    "Summarize the key points",
    "What is this document about?",
    "What are the key takeaways?",
)

def render_empty_state():

    st.html(
        '<div class="upload-shell">'
        '<h1 class="upload-title">Your documents, understood.</h1>'
        '<div class="upload-subtitle">'
        'Drop in a PDF and start a conversation with what matters.'
        '</div>'
        '</div>'
    )

    uploaded = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed",
        key=f"empty_uploader_{st.session_state.uploader_nonce}",
    )

    upload_error = st.session_state.pop("upload_error", None)

    if upload_error:
        with st.container(key="upload_error"):
            st.error(upload_error)

    chips = "".join(
        f'<span class="suggestion-chip">{html.escape(label)}</span>'
        for label in SUGGESTED_QUESTIONS
    )

    st.html(
        '<div class="upload-after">'
        f'<div class="privacy-note">{ICON_LOCK}'
        'Your files stay private. '
        'Documents are processed locally with Ollama.'
        '</div>'
        '<div class="suggestion-title">Once uploaded, try asking</div>'
        f'<div class="suggestion-row">{chips}</div>'
        '</div>'
    )

    return uploaded


# ==================================================
# CHAT HEADER
# ==================================================

def render_chat_header(
    file_name: str,
    page_count: int,
) -> None:

    pages_label = "page" if page_count == 1 else "pages"

    st.html(
        '<div class="chat-page-header">'
        '<div class="chat-page-heading">'
        '<div class="chat-page-title">Document chat</div>'
        f'<div class="chat-page-meta" title="{html.escape(file_name)}">'
        f'<span class="chat-page-file">{html.escape(file_name)}</span>'
        f'<span class="chat-page-pages">&nbsp;·&nbsp; '
        f'{page_count} {pages_label}</span>'
        '</div>'
        '</div>'
        '</div>'
    )


def render_chat_intro(
    file_name: str,
) -> None:

    st.html(
        '<div class="chat-intro">'
        '<div class="chat-kicker">'
        '<span class="kicker-dot"></span>'
        'DocuAI&nbsp;·&nbsp;'
        f'<span class="chat-kicker-file" title="{html.escape(file_name)}">'
        f'{html.escape(file_name)}</span>'
        '</div>'
        '<div class="chat-intro-title">'
        'I’ve read your document. What would you like to explore?'
        '</div>'
        '<div class="chat-intro-subtitle">'
        'Ask questions, uncover insights, '
        'and get answers grounded in your file.'
        '</div>'
        '</div>'
    )

    if st.session_state.messages:
        return

    with st.container(key="intro_suggestions", horizontal=True):
        for index, label in enumerate(SUGGESTED_QUESTIONS):
            if st.button(label, key=f"suggestion_{index}"):
                ask(label)


# ==================================================
# SOURCE CARDS
# ==================================================

def page_label(
    page: object,
) -> str:
    return f"{int(page):02d}" if str(page).isdigit() else str(page)


def render_sources(
    sources: list[dict],
) -> None:

    if not sources:
        return

    cards = "".join(
        '<div class="source-card">'
        '<div class="source-card-label">'
        f'Source {index:02d} &nbsp;·&nbsp; '
        f'Page {html.escape(page_label(source.get("page", "?")))}'
        '</div>'
        '<div class="source-card-text">'
        f'{html.escape(truncate(source_passage(source), 120))}'
        '</div>'
        '</div>'
        for index, source in enumerate(sources, start=1)
    )

    count = len(sources)
    noun = "reference" if count == 1 else "references"

    st.html(
        f'<div class="source-heading">Sources &nbsp;·&nbsp; '
        f'{count} {noun}</div>'
        f'<div class="source-grid">{cards}</div>'
    )


# ==================================================
# CHAT MESSAGE
# ==================================================

def render_message(
    index: int,
    message: dict,
    is_last: bool,
) -> None:

    if message["role"] == "user":
        st.html(
            '<div class="user-bubble">'
            f'{html.escape(message["content"])}'
            '</div>'
        )
        return

    with st.container(key=f"answer_{index}"):

        st.html(
            '<div class="assistant-meta">'
            '<span class="kicker-dot"></span>'
            f'DocuAI &nbsp;·&nbsp; {relative_time(message.get("time"))}'
            '</div>'
        )

        st.markdown(message["content"])

        render_sources(message.get("sources", []))

        is_error = message.get("error", False)

        if is_error and not is_last:
            return

        with st.container(
            key=f"actions_{index}",
            horizontal=True,
        ):

            if not is_error:

                helpful = message.get("helpful", False)

                if st.button(
                    "Helpful",
                    key=(
                        f"helpful_on_{index}"
                        if helpful
                        else f"helpful_{index}"
                    ),
                    type="tertiary",
                    icon=(
                        ":material/favorite:"
                        if helpful
                        else ":material/favorite_border:"
                    ),
                ):
                    message["helpful"] = not helpful
                    st.rerun()

            if is_last and st.button(
                "Try again" if is_error else "Regenerate",
                key=f"regenerate_{index}",
                type="tertiary",
                icon=":material/refresh:",
            ):
                st.session_state.messages.pop()
                st.rerun()


# ==================================================
# DOCUMENT PREVIEW
# ==================================================

def passage_spans(
    text: str,
    passages: list[str],
) -> list[list[int]]:
    """Merged [start, end) character spans of each passage found in text."""

    spans: list[tuple[int, int]] = []

    for passage in passages:

        words = passage.split()

        if not words:
            continue

        pattern = r"\s+".join(re.escape(word) for word in words)
        match = re.search(pattern, text)

        if match:
            spans.append(match.span())

    spans.sort()

    merged: list[list[int]] = []

    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return merged


def highlight_segment(
    text: str,
    spans: list[list[int]],
    start: int,
    end: int,
) -> str:
    """Escaped text[start:end] with the parts covered by spans in <mark>."""

    parts: list[str] = []
    cursor = start

    for span_start, span_end in spans:
        span_start = max(span_start, start)
        span_end = min(span_end, end)

        if span_start >= span_end:
            continue

        parts.append(html.escape(text[cursor:span_start]))
        parts.append(f"<mark>{html.escape(text[span_start:span_end])}</mark>")
        cursor = span_end

    parts.append(html.escape(text[cursor:end]))

    return "".join(parts)


def latest_sources() -> list[dict]:
    for message in reversed(st.session_state.messages):
        if message["role"] == "assistant":
            return message.get("sources", [])
    return []


def render_preview(
    file_name: str,
    file_size_mb: float,
    page_texts: list[str],
    page_count: int,
) -> None:

    current = max(1, min(st.session_state.preview_page, page_count))
    st.session_state.preview_page = current

    size_label = (
        f"{file_size_mb:.1f} MB"
        if file_size_mb >= 0.1
        else f"{file_size_mb * 1024:.0f} KB"
    )

    st.html(
        '<div class="preview-file-row">'
        '<div class="preview-file">'
        f'{ICON_FILE}'
        '<div style="min-width:0;">'
        f'<div class="preview-file-name" title="{html.escape(file_name)}">'
        f'{html.escape(file_name)}</div>'
        f'<div class="preview-file-meta">PDF · {size_label}</div>'
        '</div>'
        '</div>'
        '</div>'
    )

    with st.container(
        key="preview_nav",
        horizontal=True,
        vertical_alignment="center",
    ):

        if st.button(
            "",
            key="preview_prev",
            icon=":material/chevron_left:",
            disabled=current <= 1,
            help="Previous page",
        ):
            st.session_state.preview_page = current - 1
            st.rerun()

        st.html(
            f'<div class="preview-nav-label">'
            f'Page {current} of {page_count}</div>'
        )

        if st.button(
            "",
            key="preview_next",
            icon=":material/chevron_right:",
            disabled=current >= page_count,
            help="Next page",
        ):
            st.session_state.preview_page = current + 1
            st.rerun()

    page_text = (
        page_texts[current - 1]
        if current - 1 < len(page_texts)
        else ""
    )[:4000]

    # The first line is shown as the page title, the rest as the body.
    # Passages are matched on the whole page so one that starts in the
    # title line is highlighted in both.
    title_end = page_text.find("\n")
    title_end = len(page_text) if title_end == -1 else title_end
    body_start = title_end + 1

    sources = latest_sources()

    page_passages = [
        source_passage(source)
        for source in sources
        if str(source.get("page")) == str(current)
    ]

    spans = passage_spans(page_text, page_passages)
    title_markup = highlight_segment(
        page_text, spans, 0, min(title_end, 80)
    )
    body_markup = highlight_segment(
        page_text, spans, body_start, len(page_text)
    ).strip()

    stem = html.escape(Path(file_name).stem)

    if not page_text:
        title_markup = ""
        body_markup = "No extractable text on this page."

    st.html(
        '<div class="pdf-paper">'
        f'<div class="pdf-paper-kicker">{stem}</div>'
        f'<div class="pdf-paper-title">{title_markup}</div>'
        '<div class="pdf-paper-meta">'
        f'Page {current:02d} &nbsp;·&nbsp; Extracted text'
        '</div>'
        f'<div class="pdf-paper-body">{body_markup}</div>'
        f'<div class="pdf-paper-footer">DocuAI &nbsp;·&nbsp; {stem}</div>'
        '</div>'
    )

    count = len(sources)

    if count:
        noun = "passage" if count == 1 else "passages"
        st.html(
            f'<div class="preview-footer">{count} cited {noun} '
            f'&nbsp;·&nbsp; {len(spans)} on this page</div>'
        )


# ==================================================
# QUESTION → ANSWER
# ==================================================

def answer_question(
    question: str,
    vector_store: Chroma,
    chunks: list[Document],
) -> dict:

    error = validate_question(
        question
    )

    if error:
        return {
            "error": error
        }

    retrieval = retrieve_context(
        question,
        vector_store,
        chunks,
        top_k=TOP_K,
        relevance_threshold=RELEVANCE_THRESHOLD,
    )

    if "error" in retrieval:
        return {
            "error": retrieval["error"]
        }

    results = retrieval["results"]
    overview = retrieval["mode"] == "overview"

    prompt = build_prompt(
        question,
        results,
        overview=overview,
    )

    model = ChatOllama(
        model=MODEL_NAME,
        temperature=0,
    )

    model_result = (
        invoke_ollama_safely(
            model,
            prompt,
        )
    )

    if not model_result["ok"]:

        return {
            "error":
            model_result[
                "user_message"
            ]
        }

    # An overview draws on more of the document, so cite a little more.
    sources = unique_sources(
        results,
        limit=4 if overview else 3,
    )

    source_payload = [
        {
            "source":
            item.metadata.get(
                "source",
                "Unknown document",
            ),
            "page":
            item.metadata.get(
                "page",
                "?",
            ),
            "text":
            item.page_content,
        }
        for item in sources
    ]

    return {
        "answer":
        model_result[
            "content"
        ],
        "sources":
        source_payload,
    }




# ==================================================
# DOCUMENT CHAT STATE
# ==================================================

def try_open_upload(
    name: str,
    data: bytes,
) -> str | None:
    """Validate and open an uploaded PDF. Returns an error message or None."""

    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return f"This PDF is larger than {MAX_UPLOAD_MB} MB."

    try:
        load_pdf(
            hashlib.sha256(data).hexdigest(),
            data,
            name,
        )
    except ValueError as exc:
        return str(exc)

    open_document(name, data)

    return None


def answer_pending_question(
    vector_store: Chroma,
    chunks: list[Document],
) -> None:

    question = st.session_state.messages[-1]["content"]

    with st.spinner("Reading the relevant passages…"):
        result = answer_question(question, vector_store, chunks)

    if "error" in result:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": result["error"],
                "sources": [],
                "error": True,
                "time": time.time(),
            }
        )
        return

    sources = result["sources"]
    reference = f"{question} {result['answer']}"

    for source in sources:
        source["passage"] = key_passage(source["text"], reference)

    st.session_state.source_pages = [
        int(source["page"])
        for source in sources
        if str(source["page"]).isdigit()
    ]

    if st.session_state.source_pages:
        st.session_state.preview_page = st.session_state.source_pages[0]

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": sources,
            "time": time.time(),
        }
    )


def scroll_to_latest(
    message_count: int,
) -> None:
    """
    Keep the newest message in view. The message count is part of the
    markup, so the script only re-runs when the conversation grows.
    """

    st.html(
        f"<script>/* messages: {message_count} */"
        "(() => {"
        "const pane = window.parent.document.querySelector("
        "'.st-key-chat_scroll') || document.querySelector("
        "'.st-key-chat_scroll');"
        "if (pane) requestAnimationFrame(() => pane.scrollTo("
        "{top: pane.scrollHeight, behavior: 'smooth'}));"
        "})();</script>",
        unsafe_allow_javascript=True,
    )


def render_chat_state(
    document: dict,
) -> None:

    data = document["bytes"]
    name = document["name"]
    document_key = document["key"]

    page_count, page_documents, page_texts = load_pdf(
        document_key,
        data,
        name,
    )

    chunks = build_chunks(page_documents)

    with st.spinner("Preparing your document…"):
        vector_store = get_vector_store(
            document_key,
            chunks,
        )

    chat_col, preview_col = st.columns(
        [1.6, 1],
        gap=None,
    )

    # Render the preview first so it stays visible while an answer runs.
    with preview_col:
        with st.container(key="preview_panel"):
            render_preview(
                name,
                len(data) / (1024 * 1024),
                page_texts,
                page_count,
            )

    with chat_col:
        with st.container(key="chat_pane"):

            render_chat_header(name, page_count)

            with st.container(key="chat_scroll"):

                render_chat_intro(name)

                messages = st.session_state.messages

                for index, message in enumerate(messages):
                    render_message(
                        index,
                        message,
                        is_last=index == len(messages) - 1,
                    )

                if messages:
                    scroll_to_latest(len(messages))

                if messages and messages[-1]["role"] == "user":
                    answer_pending_question(vector_store, chunks)
                    st.rerun()

            with st.container(key="chat_composer"):

                submission = st.chat_input(
                    "Ask anything about this document…",
                    key=f"chat_input_{document_key}",
                    accept_file=True,
                    file_type=["pdf"],
                    max_upload_size=MAX_UPLOAD_MB,
                )

                st.html(
                    '<div class="composer-footer">'
                    '<span>↵ to send &nbsp;·&nbsp; '
                    'Answers are grounded in your files</span>'
                    '<span class="processed-note">'
                    '<span class="processed-dot"></span>'
                    'Processed locally with Ollama</span>'
                    '</div>'
                )

    if not submission:
        return

    if submission.files:
        attached = submission.files[0]
        error = try_open_upload(attached.name, attached.getvalue())

        if error:
            st.toast(error, icon=":material/error:")
            return

    question = (submission.text or "").strip()

    if question:
        ask(question)

    st.rerun()


# ==================================================
# APP ENTRY
# ==================================================

init_state()

render_sidebar()

current_document = find_document(st.session_state.current_doc_key)

if current_document is None:

    uploaded_file = render_empty_state()

    if uploaded_file is not None:

        upload_error = try_open_upload(
            uploaded_file.name,
            uploaded_file.getvalue(),
        )

        if upload_error:
            st.session_state.upload_error = upload_error

        # A fresh uploader key clears the widget for the next visit.
        st.session_state.uploader_nonce += 1
        st.rerun()

else:

    render_chat_state(current_document)
