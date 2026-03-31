import json
import uuid
import os
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.knowledge import KnowledgeDocument, KnowledgeChunk
from services.embedding_service import embedding_service
from services.vector_store import SimpleVectorStore


class KnowledgeService:
    def __init__(self):
        persist_path = os.path.join(settings.CHROMA_PERSIST_DIR, "vectors.json")
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.collection = SimpleVectorStore(persist_path)

    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(para) > chunk_size:
                    sentences = para.replace(". ", ".\n").split("\n")
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= chunk_size:
                            current_chunk = current_chunk + " " + sent if current_chunk else sent
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [c for c in chunks if len(c.strip()) > 50]

    async def ingest_document(
        self, db: AsyncSession, title: str, category: str, content: str,
        url: Optional[str] = None, phone: Optional[str] = None,
        source: str = "manual", chunk_type: str = "narrative",
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            title=title, category=category, content=content,
            url=url, phone=phone, source=source,
        )
        db.add(doc)
        await db.flush()

        text_chunks = self.chunk_text(content)
        embeddings = embedding_service.embed_batch(text_chunks)

        for i, (text, embedding) in enumerate(zip(text_chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            metadata = {
                "document_id": str(doc.id),
                "title": title,
                "category": category,
                "chunk_type": chunk_type,
                "url": url or "",
                "phone": phone or "",
                "source": source,
            }

            chunk = KnowledgeChunk(
                id=chunk_id, document_id=doc.id, content=text,
                chunk_type=chunk_type, chunk_index=i,
                metadata_json=json.dumps(metadata),
            )
            db.add(chunk)
            self.collection.add(chunk_id, embedding, text, metadata)

        await db.commit()
        return doc

    async def update_document(
        self, db: AsyncSession, doc_id: int,
        title: Optional[str] = None, category: Optional[str] = None,
        content: Optional[str] = None, url: Optional[str] = None, phone: Optional[str] = None,
    ) -> Optional[KnowledgeDocument]:
        result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return None

        content_changed = content is not None and content != doc.content

        if title is not None: doc.title = title
        if category is not None: doc.category = category
        if content is not None: doc.content = content
        if url is not None: doc.url = url
        if phone is not None: doc.phone = phone

        if content_changed:
            old_chunks = await db.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)
            )
            old_chunk_ids = [c.id for c in old_chunks.scalars().all()]
            if old_chunk_ids:
                self.collection.delete(old_chunk_ids)
            for cid in old_chunk_ids:
                cr = await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.id == cid))
                c = cr.scalar_one_or_none()
                if c: await db.delete(c)

            text_chunks = self.chunk_text(doc.content)
            embeddings = embedding_service.embed_batch(text_chunks)
            for i, (text, embedding) in enumerate(zip(text_chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                metadata = {
                    "document_id": str(doc.id), "title": doc.title,
                    "category": doc.category, "chunk_type": "narrative",
                    "url": doc.url or "", "phone": doc.phone or "", "source": doc.source,
                }
                chunk = KnowledgeChunk(
                    id=chunk_id, document_id=doc.id, content=text,
                    chunk_type="narrative", chunk_index=i,
                    metadata_json=json.dumps(metadata),
                )
                db.add(chunk)
                self.collection.add(chunk_id, embedding, text, metadata)

        await db.commit()
        return doc

    async def delete_document(self, db: AsyncSession, doc_id: int) -> bool:
        result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return False
        chunks_result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id)
        )
        chunk_ids = [c.id for c in chunks_result.scalars().all()]
        if chunk_ids:
            self.collection.delete(chunk_ids)
        await db.delete(doc)
        await db.commit()
        return True

    async def get_documents(self, db: AsyncSession, skip: int = 0, limit: int = 50):
        result = await db.execute(
            select(KnowledgeDocument).order_by(KnowledgeDocument.updated_at.desc()).offset(skip).limit(limit)
        )
        docs = result.scalars().all()
        total_result = await db.execute(select(func.count(KnowledgeDocument.id)))
        total = total_result.scalar()
        return docs, total

    async def get_document(self, db: AsyncSession, doc_id: int):
        result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        return result.scalar_one_or_none()

    def get_collection_count(self) -> int:
        return self.collection.count()


knowledge_service = KnowledgeService()
