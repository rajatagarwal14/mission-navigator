from fastapi import APIRouter
from services.knowledge_service import knowledge_service

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Mission Navigator",
        "version": "1.0.0",
        "knowledge_base_chunks": knowledge_service.get_collection_count(),
    }
