import google.generativeai as genai
from functools import lru_cache
from typing import List

from config import settings


class EmbeddingService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = "models/gemini-embedding-001"

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    def embed_query(self, query: str) -> List[float]:
        """Embed a query (uses retrieval_query task type for better results)."""
        result = genai.embed_content(
            model=self.model,
            content=query,
            task_type="retrieval_query",
        )
        return result["embedding"]

    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """Embed multiple texts in a batch."""
        results = []
        # Process in batches of 100 (API limit)
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            batch_result = genai.embed_content(
                model=self.model,
                content=batch,
                task_type=task_type,
            )
            results.extend(batch_result["embedding"])
        return results


embedding_service = EmbeddingService()
