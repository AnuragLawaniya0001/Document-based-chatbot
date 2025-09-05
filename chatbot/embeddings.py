import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GENAI_API_KEY"])

def load_embedding_model():
    return "gemini-embeddings"

def embed_texts(chunks, model="models/embedding-001"):
    embeddings = []
    for chunk in chunks:
        response = genai.embed_content(
            model=model,
            content=chunk,
            task_type="retrieval_document"
        )
        embeddings.append(response["embedding"])
    return embeddings
