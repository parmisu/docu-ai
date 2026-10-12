import streamlit as st
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama

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

    # Read the PDF
    reader = PdfReader(uploaded_file)

    st.write(f"Number of pages: {len(reader.pages)}")

    # Extract text from all pages
    full_text = ""

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text:
            full_text += f"\n--- Page {page_number} ---\n"
            full_text += page_text

    # Split the extracted text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = text_splitter.split_text(full_text)

    st.write(f"Number of chunks: {len(chunks)}")

    # Show the first few chunks
    st.subheader("Text Chunks")

    for i, chunk in enumerate(chunks[:5], start=1):
        with st.expander(f"Chunk {i}"):
            st.write(chunk)

       # Create embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Store chunk embeddings inside Chroma
    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings
    )

    # Ask a question
    question = st.text_input(
        "Ask a question about the document"
    )

    # Search for the most relevant chunks
    if question:
     results = vector_store.similarity_search(
        question,
        k=3
    )

    context = "\n\n".join(
        result.page_content for result in results
    )

    llm = ChatOllama(
        model="llama3.2:1b",
        temperature=0
    )

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the context below.

If the answer is not contained in the context, say:
"I could not find the answer in the uploaded document."

Context:
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
        with st.expander(f"Source {i}"):
            st.write(result.page_content)