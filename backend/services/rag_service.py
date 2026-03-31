from typing import List, Dict, Any, Optional
from services.embedding_service import embedding_service
from services.knowledge_service import knowledge_service


class RAGService:
    # Category keywords for metadata boosting
    CATEGORY_KEYWORDS = {
        "Mental Health": ["mental health", "ptsd", "depression", "anxiety", "therapy", "counseling", "treatment", "tbi"],
        "Child & Youth": ["child", "children", "kid", "youth", "teen", "son", "daughter", "school"],
        "Caregiver Support": ["caregiver", "caring for", "taking care", "burnout", "respite"],
        "Illinois-Specific": ["illinois", "chicago", "il", "local"],
        "Financial & Practical": ["financial", "money", "rent", "food", "emergency fund", "bills", "employment", "job"],
        "Educational Support": ["education", "school", "scholarship", "tuition", "degree", "ged"],
        "LGBTQ+ Resources": ["lgbtq", "gay", "lesbian", "transgender", "queer", "bisexual"],
        "Crisis Support": ["crisis", "emergency", "urgent", "immediate help", "988"],
        "Comprehensive Support": ["military onesource", "general help", "where to start", "don't know where"],
    }

    def detect_category(self, query: str) -> Optional[str]:
        """Detect the most likely category from the query."""
        query_lower = query.lower()
        best_category = None
        best_count = 0

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in query_lower)
            if count > best_count:
                best_count = count
                best_category = category

        return best_category if best_count > 0 else None

    def _keyword_fallback(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Fallback keyword-based search when embedding API is unavailable."""
        query_lower = query.lower()
        words = set(query_lower.split())
        scored = []
        for id, entry in knowledge_service.collection.vectors.items():
            doc_lower = entry["document"].lower()
            title_lower = entry["metadata"].get("title", "").lower()
            # Score based on word matches
            score = sum(2 for w in words if w in title_lower) + sum(1 for w in words if w in doc_lower)
            if score > 0:
                scored.append({
                    "chunk_id": id,
                    "content": entry["document"],
                    "metadata": entry["metadata"],
                    "similarity": min(score / 10, 1.0),
                    "final_score": min(score / 10, 1.0),
                })
        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored[:n_results]

    def retrieve(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query using vector similarity + metadata boosting."""
        # Try to embed the query; fall back to keyword search if API unavailable
        try:
            query_embedding = embedding_service.embed_query(query)
        except Exception as e:
            print(f"Embedding failed, using keyword fallback: {e}")
            return self._keyword_fallback(query, n_results)

        # Detect category for metadata boosting
        detected_category = self.detect_category(query)

        candidates_count = min(n_results * 2, 15)

        results = knowledge_service.collection.query(
            query_embedding=query_embedding,
            n_results=candidates_count,
        )

        if not results or not results["ids"] or not results["ids"][0]:
            return self._keyword_fallback(query, n_results)

        # Build candidate list with scores
        candidates = []
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            document = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Convert cosine distance to similarity (ChromaDB returns distance)
            similarity = 1 - distance

            # Calculate boosted score
            category_boost = 0.0
            if detected_category and metadata.get("category") == detected_category:
                category_boost = 0.15

            chunk_type_boost = 0.0
            if metadata.get("chunk_type") == "resource":
                chunk_type_boost = 0.08
            elif metadata.get("chunk_type") == "crisis":
                chunk_type_boost = 0.12

            final_score = (0.7 * similarity) + (0.2 * category_boost) + (0.1 * chunk_type_boost)

            candidates.append({
                "chunk_id": chunk_id,
                "content": document,
                "metadata": metadata,
                "similarity": similarity,
                "final_score": final_score,
            })

        # Sort by final score and take top N
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        return candidates[:n_results]

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a context string for the LLM."""
        if not chunks:
            return "No relevant information found in the knowledge base."

        context_parts = []
        for chunk in chunks:
            meta = chunk["metadata"]
            part = f"**Resource: {meta.get('title', 'Unknown')}**\n"
            part += f"Category: {meta.get('category', 'General')}\n"
            if meta.get("phone"):
                part += f"Phone: {meta['phone']}\n"
            if meta.get("url"):
                part += f"URL: {meta['url']}\n"
            part += f"\n{chunk['content']}\n"
            context_parts.append(part)

        return "\n---\n".join(context_parts)

    def extract_resource_info(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract resource information for the response."""
        seen = set()
        resources = []
        for chunk in chunks:
            meta = chunk["metadata"]
            name = meta.get("title", "")
            if name and name not in seen:
                seen.add(name)
                resources.append({
                    "name": name,
                    "category": meta.get("category", ""),
                    "description": chunk["content"][:200],
                    "phone": meta.get("phone", ""),
                    "url": meta.get("url", ""),
                })
        return resources


rag_service = RAGService()
