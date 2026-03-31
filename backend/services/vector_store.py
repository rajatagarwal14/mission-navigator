"""Lightweight JSON-file-based vector store. No native dependencies required.
Replaces ChromaDB for MVP deployments where native builds are problematic."""

import json
import math
import os
from typing import List, Dict, Any, Optional


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SimpleVectorStore:
    """In-memory vector store backed by a JSON file for persistence."""

    def __init__(self, persist_path: str):
        self.persist_path = persist_path
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.persist_path):
            with open(self.persist_path, "r") as f:
                self.vectors = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        with open(self.persist_path, "w") as f:
            json.dump(self.vectors, f)

    def add(self, id: str, embedding: List[float], document: str, metadata: Dict[str, str]):
        self.vectors[id] = {
            "embedding": embedding,
            "document": document,
            "metadata": metadata,
        }
        self._save()

    def add_batch(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, str]]):
        for id, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self.vectors[id] = {
                "embedding": emb,
                "document": doc,
                "metadata": meta,
            }
        self._save()

    def delete(self, ids: List[str]):
        for id in ids:
            self.vectors.pop(id, None)
        self._save()

    def query(self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, List]:
        """Query the vector store. Returns dict with ids, documents, metadatas, distances."""
        results = []

        for id, entry in self.vectors.items():
            # Apply metadata filter if provided
            if where:
                match = True
                for key, value in where.items():
                    if entry["metadata"].get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            similarity = cosine_similarity(query_embedding, entry["embedding"])
            distance = 1 - similarity  # cosine distance
            results.append({
                "id": id,
                "document": entry["document"],
                "metadata": entry["metadata"],
                "distance": distance,
            })

        # Sort by distance (ascending = most similar first)
        results.sort(key=lambda x: x["distance"])
        top = results[:n_results]

        return {
            "ids": [[r["id"] for r in top]],
            "documents": [[r["document"] for r in top]],
            "metadatas": [[r["metadata"] for r in top]],
            "distances": [[r["distance"] for r in top]],
        }

    def count(self) -> int:
        return len(self.vectors)
