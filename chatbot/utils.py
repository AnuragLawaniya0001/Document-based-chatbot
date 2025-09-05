from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

def retrieve_documents(query_embedding: np.ndarray, doc_embeddings: np.ndarray, chunks: List[str], top_k: int = 4) -> List[str]:
    sims = cosine_similarity([query_embedding], doc_embeddings)[0]
    top_indices = sims.argsort()[-top_k:][::-1]
    return [chunks[i] for i in top_indices]
