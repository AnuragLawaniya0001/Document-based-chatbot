import streamlit as st
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import google.generativeai as genai


st.set_page_config(page_title="RAG Chat with Documents", page_icon="📚", layout="wide")

# Initialize embedding model - use sentence transformers model
@st.cache_resource(show_spinner=False)
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

# Helper to split document text into chunks for retrieval
def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks

# Helper: Embed list of texts
def embed_texts(texts: List[str], model) -> np.ndarray:
    embeddings = model.encode(texts)
    # Normalize embeddings for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings

# Retrieve top k most similar chunks given query embedding and document embeddings
def retrieve_documents(
    query_embedding: np.ndarray,
    doc_embeddings: np.ndarray,
    chunks: List[str],
    top_k: int = 4
) -> List[str]:
    sims = cosine_similarity([query_embedding], doc_embeddings)[0]
    top_indices = sims.argsort()[-top_k:][::-1]
    return [chunks[i] for i in top_indices]

# Generate answer using Gemini API
def generate_answer_gemini(context: str, query: str, api_key: str) -> str:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        prompt = f"""You are a helpful assistant that answers questions based on the provided document context.

Context:
{context}

Question: {query}
Answer:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"


# Simple fallback answer generator (echo with context)
def generate_answer_fallback(context: str, query: str) -> str:
    return f"Simulated answer based on retrieved content:\n\n{context[:1000]}..."

# Main Streamlit app
def main():
    st.title("📚 Retrieval Augmented Generation (RAG) Chat with Your Documents")
    st.write(
        """
        Upload multiple documents and chat with their content using a Retrieval Augmented Generation approach.
        Powered by embeddings and GPT-based generation.
        """
    )

    if "docs_chunks" not in st.session_state:
        st.session_state.docs_chunks = []
    if "docs_embeddings" not in st.session_state:
        st.session_state.docs_embeddings = np.array([])
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    embedding_model = load_embedding_model()

    with st.sidebar:
        st.header("1. Upload Documents")
        uploaded_files = st.file_uploader("Upload your documents (txt, pdf supported)", type=['txt','pdf'], accept_multiple_files=True)
        process_button = st.button("Process Documents")

        st.markdown("---")
        st.header("2. Enter Gemini API Key (optional)")
        gemini_api_key = st.text_input("Gemini API Key", type="password")
        if gemini_api_key:
            st.success("API Key detected. Gemini responses will be generated.")
        else:
            st.info("API key not provided, using fallback answer generation.")

    # Load and process uploaded docs if button clicked
    if process_button and uploaded_files:
        all_chunks = []
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_extension = file_name.split('.')[-1].lower()
            raw_text = ""
            try:
                if file_extension == 'txt':
                    raw_text = uploaded_file.getvalue().decode("utf-8")
                elif file_extension == 'pdf':
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text_pages = []
                    for page in pdf_reader.pages:
                        text_pages.append(page.extract_text())
                    raw_text = "\n".join(text_pages)
                else:
                    st.warning(f"Unsupported file type for {file_name}, skipping.")
                    continue
            except Exception as e:
                st.error(f"Error reading {file_name}: {str(e)}")
                continue

            chunks = split_text(raw_text)
            all_chunks.extend(chunks)

        if all_chunks:
            embeddings = embed_texts(all_chunks, embedding_model)
            st.session_state.docs_chunks = all_chunks
            st.session_state.docs_embeddings = embeddings
            st.success(f"Processed {len(all_chunks)} text chunks from uploaded documents.")
            st.session_state.chat_history = []
        else:
            st.warning("No text content extracted from uploaded files.")

    # Chat interface
    st.header("💬 Chat with Documents")

    def submit_query():
        user_query = st.session_state.user_query.strip()
        if not user_query:
            return

        st.session_state.user_query = ""

        if len(st.session_state.docs_chunks) == 0:
            st.warning("No documents processed yet. Please upload and process files first.")
            return

        query_emb = embedding_model.encode([user_query])
        query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)

        retrieved_chunks = retrieve_documents(query_emb[0], st.session_state.docs_embeddings, st.session_state.docs_chunks, top_k=4)
        context_for_generation = "\n---\n".join(retrieved_chunks)

        if gemini_api_key:
            answer = generate_answer_gemini(context_for_generation, user_query, gemini_api_key)
        else:
            answer = generate_answer_fallback(context_for_generation, user_query)

        st.session_state.chat_history.append(("User", user_query))
        st.session_state.chat_history.append(("Bot", answer))

    st.text_input("Ask a question about the documents:", key="user_query", on_change=submit_query)

    chat_placeholder = st.container()

    with chat_placeholder:
        if st.session_state.chat_history:
            for role, msg in st.session_state.chat_history:
                if role == "User":
                    st.markdown(f"<div style='text-align: right; margin: 10px 0;'><b>You:</b> {msg}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"""
                        <div style='text-align: left; margin: 10px 0; padding: 10px; background-color: #e0ffe0; border-radius: 8px;'>
                            <b>Bot:</b> {msg}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
            st.info("Upload and process documents to start chatting.")

if __name__ == "__main__":
    main()

