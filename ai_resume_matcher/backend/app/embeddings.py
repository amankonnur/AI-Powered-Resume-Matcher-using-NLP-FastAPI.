# app/embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import os
import pickle

MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight and good for semantic similarity

class EmbeddingIndex:
    def __init__(self, dim=384, index_path="faiss.index", meta_path="meta.pkl"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.model = SentenceTransformer(MODEL_NAME)
        # use IndexFlatIP for cosine (after normalization) / or IndexHNSWFlat for performance
        self.index = faiss.IndexFlatIP(self.dim)  # inner product on normalized vectors
        self.metadatas = []  # list of dicts, same order as vectors

    def encode(self, texts):
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        # normalize for cosine
        faiss.normalize_L2(embs)
        return embs

    def add(self, texts, metadatas):
        vecs = self.encode(texts)
        self.index.add(vecs)
        self.metadatas.extend(metadatas)
        self._save()

    def search(self, text, top_k=5):
        vec = self.encode([text])
        D, I = self.index.search(vec, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            meta = self.metadatas[idx]
            results.append({"score": float(score), "meta": meta})
        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.metadatas = pickle.load(f)
