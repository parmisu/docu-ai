import streamlit as st
from pypdf import PdfReader

from langchain_text_splitters import RecursiveCharacterTextSplitter

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

    full_text = ""

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            full_text += f"\n--- Page {page_number} ---\n"
            full_text += page_text

    # st.subheader("Extracted Text")

    # st.text_area(
    #     "PDF Content",
    #     full_text,
    #     height=400
    # )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_text(full_text)

    st.write(f"Number of chunks: {len(chunks)}")

    st.subheader("Text Chunks")

    for i, chunk in enumerate(chunks[:5], start=1):
        with st.expander(f"Chunk {i}"):
            st.write(chunk)