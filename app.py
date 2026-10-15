import streamlit as st

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.documents import Document


st.set_page_config(
    page_title="Docu AI",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Docu AI")
st.write("Upload your documents and ask questions about them.")


uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)


if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")

    reader = PdfReader(uploaded_file)

    st.write(f"Number of pages: {len(reader.pages)}")

    # Create one LangChain Document per PDF page
    page_documents = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            page_documents.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "source": uploaded_file.name,
                        "page": page_number
                    }
                )
            )

    # Split each page while preserving metadata
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_documents(page_documents)

    st.write(f"Number of chunks: {len(chunks)}")

    # Show first few chunks for debugging
    st.subheader("Text Chunks")

    for i, chunk in enumerate(chunks[:5], start=1):
        with st.expander(
            f"Chunk {i} — Page {chunk.metadata['page']}"
        ):
            st.write(chunk.page_content)

    # Local embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Store chunks + metadata in Chroma
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    question = st.text_input(
        "Ask a question about the document"
    )

    if question:
        results = vector_store.similarity_search(
            question,
            k=5
        )

        context = "\n\n".join(
            f"[Page {result.metadata['page']}]\n{result.page_content}"
            for result in results
        )

        llm = ChatOllama(
            model="llama3.2:3b",
            temperature=0
        )

        prompt = f"""
Answer the question using only the document context below.

Use all relevant information from the context.
If the document contains a list, reproduce the complete list.
Do not invent information.

If the answer truly does not appear in the context, say:
"I could not find the answer in the uploaded document."

Document context:
{context}

Question:
{question}

Answer:
"""

        response = llm.invoke(prompt)

        st.subheader("Answer")
        st.write(response.content)

        st.subheader("Sources")

        for i, result in enumerate(results, start=1):
            source_name = result.metadata.get(
                "source",
                "Unknown document"
            )

            page_number = result.metadata.get(
                "page",
                "Unknown page"
            )

            with st.expander(
                f"Source {i} — {source_name} — Page {page_number}"
            ):
                st.write(result.page_content)