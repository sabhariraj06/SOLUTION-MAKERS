from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load the embedding model once globally
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # or any model you prefer

def retrieve_top_k(query, index, chunks, k=3):
    # Encode query
    query_emb = embedding_model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_emb)

    # Search FAISS index
    D, I = index.search(query_emb, k)

    # Return top-k chunks
    results = [chunks[i] for i in I[0]]
    return results
