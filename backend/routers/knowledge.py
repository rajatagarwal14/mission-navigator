from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import StaffUser
from models.knowledge import KnowledgeDocument, KnowledgeChunk
from core.security import get_current_user
from schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentList,
)
from services.knowledge_service import knowledge_service

router = APIRouter(prefix="/api/admin/knowledge", tags=["knowledge"])


@router.get("", response_model=KnowledgeDocumentList)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """List all knowledge base documents."""
    docs, total = await knowledge_service.get_documents(db, skip=skip, limit=limit)

    items = []
    for doc in docs:
        chunk_count = await db.execute(
            select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == doc.id)
        )
        items.append(KnowledgeDocumentResponse(
            id=doc.id,
            title=doc.title,
            category=doc.category,
            content=doc.content,
            url=doc.url,
            phone=doc.phone,
            source=doc.source,
            chunks_count=chunk_count.scalar() or 0,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ))

    return KnowledgeDocumentList(documents=items, total=total)


@router.post("", response_model=KnowledgeDocumentResponse)
async def create_document(
    body: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Add a new document to the knowledge base."""
    doc = await knowledge_service.ingest_document(
        db=db,
        title=body.title,
        category=body.category,
        content=body.content,
        url=body.url,
        phone=body.phone,
        source="manual",
    )

    chunk_count = await db.execute(
        select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == doc.id)
    )
    return KnowledgeDocumentResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        content=doc.content,
        url=doc.url,
        phone=doc.phone,
        source=doc.source,
        chunks_count=chunk_count.scalar() or 0,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.put("/{doc_id}", response_model=KnowledgeDocumentResponse)
async def update_document(
    doc_id: int,
    body: KnowledgeDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Update an existing knowledge base document."""
    doc = await knowledge_service.update_document(
        db=db,
        doc_id=doc_id,
        title=body.title,
        category=body.category,
        content=body.content,
        url=body.url,
        phone=body.phone,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_count = await db.execute(
        select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == doc.id)
    )
    return KnowledgeDocumentResponse(
        id=doc.id,
        title=doc.title,
        category=doc.category,
        content=doc.content,
        url=doc.url,
        phone=doc.phone,
        source=doc.source,
        chunks_count=chunk_count.scalar() or 0,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Delete a document from the knowledge base."""
    deleted = await knowledge_service.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": doc_id}
