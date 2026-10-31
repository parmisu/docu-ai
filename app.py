import re
import streamlit as st

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
@st.cache_resource
def get_vector_store(_documents):
    embeddings = get_embeddings()

    return Chroma.from_documents(
        documents=_documents,
        embedding=embeddings
    )

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from pdf_validation import has_pdf_signature

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Docu AI",
    page_icon="✦",
    layout="centered",
)


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown(
    """
<style>

/* ---------- GLOBAL ---------- */

.stApp {
    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(222, 230, 255, 0.68),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 8%,
            rgba(244, 226, 255, 0.62),
            transparent 28%
        ),
        linear-gradient(
            180deg,
            #fcfcff 0%,
            #f7f8fd 100%
        );
    color: #282b38;

    /* ---------- ASK BUTTON ---------- */

[data-testid="stFormSubmitButton"] {
    display: flex;
    justify-content: flex-end;
    margin-top: 0.6rem;
}

[data-testid="stFormSubmitButton"] button {
    width: auto !important;

    border: none !important;

    border-radius: 16px !important;

    background:
        linear-gradient(
            135deg,
            #e7edff,
            #f3e3ff
        ) !important;

    color:
        #454a5f !important;

    font-weight:
        700 !important;

    padding:
        0.7rem 1.15rem !important;

    box-shadow:
        0 10px 26px rgba(95, 103, 160, 0.10);

    transition:
        transform 0.18s ease,
        box-shadow 0.2s ease;
}

[data-testid="stFormSubmitButton"] button:hover {
    transform:
        translateY(-2px);

    box-shadow:
        0 14px 32px rgba(95, 103, 160, 0.15);
}

[data-testid="stFormSubmitButton"] button:active {
    transform:
        scale(0.97);
}
}

.block-container {
    max-width: 760px;
    margin: 0 auto;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
}

html {
    scroll-behavior: smooth;
}


/* ---------- HERO ---------- */

.hero {
    max-width: 680px;
    margin: 0 auto;
    text-align: center;
    padding: 1.2rem 0 1.8rem 0;
    animation: fadeUp 0.65s ease both;
}

.hero-title {
    font-size: 2.15rem;
    line-height: 1.1;
    font-weight: 760;
    letter-spacing: -0.045em;
    margin: 0;
    color: #262936;
}

.hero-subtitle {
    margin-top: 0.65rem;
    font-size: 1rem;
    color: #7b8091;
}


/* ---------- LOCAL BADGE ---------- */

.local-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;

    margin-top: 0.9rem;
    padding: 0.42rem 0.72rem;

    border-radius: 999px;

    background: rgba(255,255,255,0.78);

    border: 1px solid rgba(184,190,214,0.42);

    backdrop-filter: blur(14px);

    color: #666b7b;
    font-size: 0.8rem;

    box-shadow: 0 8px 22px rgba(80,86,130,0.06);
}

.status-dot {
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #89d7aa;

    box-shadow:
        0 0 0 5px rgba(137, 215, 170, 0.12);
}


/* ---------- GENERAL CARD ---------- */

.glass-card {
    max-width: 680px;
    margin: 1rem auto;

    background:
        rgba(255, 255, 255, 0.78);

    backdrop-filter: blur(18px);

    border:
        1px solid rgba(190, 196, 220, 0.42);

    border-radius: 24px;

    padding: 1.25rem 1.35rem;

    box-shadow:
        0 16px 44px rgba(69, 75, 112, 0.07);

    animation:
        fadeUp 0.5s ease both;
}

.glass-card:hover {
    transform: translateY(-2px);

    box-shadow:
        0 22px 55px rgba(69, 75, 112, 0.1);
}


/* ---------- LABELS ---------- */

.section-label {
    font-size: 0.76rem;

    text-transform: uppercase;

    letter-spacing: 0.13em;

    font-weight: 800;

    color: #9b9faf;

    margin-bottom: 0.55rem;
}

.doc-name {
    font-size: 1.02rem;
    font-weight: 700;

    color: #333746;
}

.doc-meta {
    margin-top: 0.3rem;

    color: #8a8f9f;

    font-size: 0.88rem;
}


/* ---------- FILE UPLOADER ---------- */

[data-testid="stFileUploader"] {
    max-width: 680px;

    margin-left: auto;
    margin-right: auto;

    background:
        rgba(255, 255, 255, 0.75);

    border:
        1px solid rgba(188, 194, 218, 0.42);

    border-radius: 24px;

    padding: 0.85rem;

    box-shadow:
        0 16px 42px rgba(69, 75, 112, 0.065);

    transition:
        transform 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    transform: translateY(-2px);

    border-color:
        rgba(164, 175, 238, 0.75);

    box-shadow:
        0 21px 52px rgba(86, 94, 148, 0.11);
}

[data-testid="stFileUploader"] button {
    border: none !important;

    border-radius: 16px !important;

    background:
        linear-gradient(
            135deg,
            #e8edff,
            #f5e6ff
        ) !important;

    color: #484d63 !important;

    font-weight: 700 !important;

    transition:
        transform 0.16s ease,
        box-shadow 0.2s ease;
}

[data-testid="stFileUploader"] button:hover {
    transform:
        translateY(-1px)
        scale(1.02);

    box-shadow:
        0 9px 24px rgba(108, 117, 177, 0.15);
}

[data-testid="stFileUploader"] button:active {
    transform: scale(0.97);
}


/* ---------- QUESTION COMPOSER ---------- */

.stTextInput {
    max-width: 680px;
    margin: 0.9rem auto 0 auto;
}

.stTextInput label {
    display: none;
}

.stTextInput > div {
    position: relative;
}

.stTextInput > div > div {
    border-radius: 24px !important;
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(186, 191, 216, 0.48) !important;

    box-shadow:
        0 14px 36px rgba(72, 78, 119, 0.07);

    transition:
        transform 0.2s ease,
        box-shadow 0.22s ease,
        border-color 0.22s ease;
}

.stTextInput > div > div:hover {
    transform: translateY(-2px);

    border-color:
        rgba(161, 173, 236, 0.8) !important;

    box-shadow:
        0 18px 44px rgba(82, 89, 146, 0.1);
}

.stTextInput > div > div:focus-within {
    transform: translateY(-2px);

    border-color:
        #b5b9ff !important;

    box-shadow:
        0 0 0 4px rgba(181, 185, 255, 0.12),
        0 20px 48px rgba(87, 93, 150, 0.12);
}

.stTextInput input {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;

    padding:
        1rem 1.1rem !important;

    font-size:
        1rem !important;

    color:
        #303442 !important;
}

.stTextInput input::placeholder {
    color:
        #a2a7b5 !important;
}


/* ---------- ANSWER CONTAINER ---------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    max-width: 680px;

    margin:
        0.7rem auto 0 auto;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.95),
            rgba(247,248,255,0.90)
        );

    border:
        1px solid rgba(188,195,221,0.42) !important;

    border-radius:
        24px !important;

    padding:
        1.1rem 1.25rem !important;

    box-shadow:
        0 18px 46px rgba(71,76,116,0.075);

    animation:
        answerIn 0.5s cubic-bezier(.2,.8,.2,1) both;

    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform:
        translateY(-2px);

    box-shadow:
        0 22px 56px rgba(71,76,116,0.105);
}

[data-testid="stVerticalBlockBorderWrapper"]
[data-testid="stVerticalBlock"] {
    gap: 0.45rem;
}


/* ---------- SOURCES ---------- */

details {
    width: 100%;
    max-width: 650px;

    margin:
        0 auto 0.55rem auto !important;

    border-radius:
        17px !important;

    border:
        1px solid rgba(190,196,216,0.45) !important;

    background:
        rgba(255,255,255,0.76) !important;

    overflow: hidden;

    box-shadow: none !important;

    transition:
        transform 0.18s ease,
        background 0.2s ease,
        box-shadow 0.2s ease,
        border-color 0.2s ease;
}

details:hover {
    transform:
        translateY(-2px);

    background:
        rgba(250,250,255,0.94) !important;

    border-color:
        rgba(166,176,236,0.72) !important;

    box-shadow:
        0 10px 28px rgba(87,93,140,0.07) !important;
}

details summary {
    font-size:
        0.91rem;

    color:
        #626879;

    cursor:
        pointer;
}


/* ---------- SPINNER ---------- */

[data-testid="stSpinner"] {
    max-width: 680px;

    margin-left: auto;
    margin-right: auto;

    padding:
        0.6rem 0;
}


/* ---------- ANIMATIONS ---------- */

@keyframes fadeUp {

    from {
        opacity: 0;
        transform:
            translateY(12px);
    }

    to {
        opacity: 1;
        transform:
            translateY(0);
    }
}

@keyframes answerIn {

    from {
        opacity: 0;

        transform:
            translateY(16px)
            scale(0.987);
    }

    to {
        opacity: 1;

        transform:
            translateY(0)
            scale(1);
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ==================================================
# HERO
# ==================================================

st.markdown(
    """
<div class="hero">
<h1 class="hero-title">Docu AI</h1>
<div class="hero-subtitle">Ask your documents anything.</div>
<div class="local-badge">
<span class="status-dot"></span>
Local AI · Private · Runs on device
</div>
</div>
""",
    unsafe_allow_html=True,
)


# ==================================================
# UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    label_visibility="collapsed",
)


# ==================================================
# DOCUMENT PROCESSING
# ==================================================
question = ""
submitted = False

if uploaded_file is not None:
    if not has_pdf_signature(uploaded_file):
        st.error(
            "The uploaded file is not a valid PDF. "
            "Please upload a genuine PDF document."
        )
        st.stop()
        
    with st.spinner("Reading your document..."):

        try:
            reader = PdfReader(uploaded_file)

            page_documents = []

            for page_number, page in enumerate(
                reader.pages,
                start=1,
            ):

                try:
                    page_text = page.extract_text()

                except Exception:
                    st.error(
                        "The PDF could not be read correctly. "
                        "One or more pages may be corrupted or incomplete."
                    )
                    st.stop()

                if page_text:

                    page_documents.append(
                        Document(
                            page_content=page_text,
                            metadata={
                                "source": uploaded_file.name,
                                "page": page_number,
                            },
                        )
                    )

        except Exception:
            st.error(
                "This PDF could not be opened. "
                "The file may be corrupted, incomplete, "
                "or not a valid PDF."
            )
            st.stop()


    if not page_documents:
        st.warning(
            "No extractable text was found in this PDF. "
            "The document may be empty, scanned, or image-only. "
            "OCR is not currently supported."
        )
        st.stop()


    # ----------------------------------------------
    # CHUNKING
    # ----------------------------------------------

    with st.spinner("Preparing document context..."):

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        chunks = text_splitter.split_documents(
            page_documents
        )
    # ----------------------------------------------
    # DOCUMENT STATUS CARD
    # ----------------------------------------------

    st.markdown(
        (
            '<div class="glass-card">'
            '<div class="section-label">'
            'Document ready'
            '</div>'
            '<div class="doc-name">'
            f'📄 {uploaded_file.name}'
            '</div>'
            '<div class="doc-meta">'
            f'{len(reader.pages)} pages'
            ' · '
            f'{len(chunks)} chunks'
            ' · Ready to search'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


    # ----------------------------------------------
    # EMBEDDINGS + VECTOR STORE
    # ----------------------------------------------

    with st.spinner("Creating semantic index..."):
         vector_store = get_vector_store(chunks)


    # ----------------------------------------------
    # QUESTION
    # ----------------------------------------------

        # ----------------------------------------------
    # QUESTION FORM
    # ----------------------------------------------

    with st.form("question_form"):

        question = st.text_input(
            "Ask a question about the document",
            placeholder="Ask anything about your document...",
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button("Ask")

    clean_question = question.strip()

    # ==================================================
    # VALIDATION + RAG
    # ==================================================

if submitted and clean_question:

        has_letters_or_numbers = bool(
            re.search(
                r"[A-Za-z0-9]",
                clean_question
            )
        )

        # ------------------------------------------
        # BASIC VALIDATION
        # ------------------------------------------

        if len(clean_question) < 3:

            st.warning(
                "Please enter a longer question."
            )


        elif not has_letters_or_numbers:

            st.warning(
                "Please enter a question using words, "
                "not only emojis or symbols."
            )


        elif len(clean_question) > 500:

            st.warning(
                "Your question is too long. "
                "Please keep it under 500 characters."
            )


        else:

            # --------------------------------------
            # SEMANTIC RETRIEVAL
            # --------------------------------------

            scored_results = (
                vector_store
                .similarity_search_with_relevance_scores(
                    clean_question,
                    k=5,
                )
            )


            if not scored_results:

                st.warning(
                    "I couldn't find anything relevant "
                    "in this document."
                )


            else:

                best_score = scored_results[0][1]

                # Temporary threshold for this local setup.
                # We can tune this after testing.
                if best_score < 0.15:

                    st.warning(
                        "I couldn't find anything relevant "
                        "to that question in this document."
                    )


                else:

                    results = [
                        document
                        for document, score in scored_results
                    ]


                    context = "\n\n".join(
                        (
                            f"[Page "
                            f"{result.metadata.get('page', 'Unknown')}"
                            f"]\n"
                            f"{result.page_content}"
                        )
                        for result in results
                    )


                    # ----------------------------------
                    # GENERATION
                    # ----------------------------------

                    with st.spinner("Thinking..."):

                        llm = ChatOllama(
                            model="llama3.2:3b",
                            temperature=0,
                        )


                        prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the document context below.

Rules:
- Use all relevant information from the context.
- Preserve the structure and meaning of the source.
- If the source contains a numbered list or table, follow that structure.
- Do not split acceptance criteria into separate items unless the source lists them separately.
- Do not invent information.
- If the answer truly does not appear in the context, say:
  "I could not find the answer in the uploaded document."

Document context:
{context}

Question:
{clean_question}

Answer:
"""


                        response = llm.invoke(
                            prompt
                        )


                    # ----------------------------------
                    # ANSWER
                    # ----------------------------------

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            '<div class="section-label">Answer</div>',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            response.content
                        )


                    # ----------------------------------
                    # UNIQUE SOURCES
                    # ----------------------------------

                    unique_sources = {}


                    for result in results:

                        source_name = (
                            result.metadata.get(
                                "source",
                                "Unknown document",
                            )
                        )

                        page_number = (
                            result.metadata.get(
                                "page",
                                "Unknown page",
                            )
                        )

                        key = (
                            source_name,
                            page_number,
                        )

                        if key not in unique_sources:

                            unique_sources[key] = result


                    # ----------------------------------
                    # SOURCE LABEL
                    # ----------------------------------

                    st.markdown(
                        (
                            '<div class="section-label" '
                            'style="max-width:650px; '
                            'margin:1.5rem auto 0.7rem auto;">'
                            'Sources'
                            '</div>'
                        ),
                        unsafe_allow_html=True,
                    )


                    # ----------------------------------
                    # SOURCE CARDS
                    # ----------------------------------

                    for result in unique_sources.values():

                        source_name = (
                            result.metadata.get(
                                "source",
                                "Unknown document",
                            )
                        )

                        page_number = (
                            result.metadata.get(
                                "page",
                                "Unknown page",
                            )
                        )

                        with st.expander(
                            f"Page {page_number} · {source_name}"
                        ):

                            st.write(
                                result.page_content
                            )


# ==================================================
# EMPTY STATE
# ==================================================
