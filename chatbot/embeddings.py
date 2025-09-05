from sentence_transformers import SentenceTransformer
import numpy as np

def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def embed_texts(texts, model):
    embeddings = model.encode(texts)
    # Normalize for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings