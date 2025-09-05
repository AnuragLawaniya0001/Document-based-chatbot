import google.generativeai as genai
from decouple import config

# ✅ Configure Gemini API
genai.configure(api_key=config("GENAI_API_KEY", default=""))

# ✅ Always return the correct embedding model
def load_embedding_model():
    return "models/embedding-001"

# ✅ Embed a list of text chunks
def embed_texts(chunks, model=None):
    if model is None:
        model = load_embedding_model()

    embeddings = []
    for chunk in chunks:
        response = genai.embed_content(
            model=model,
            content=chunk,
            task_type="retrieval_document"
        )
        embeddings.append(response["embedding"])
    return embeddings
