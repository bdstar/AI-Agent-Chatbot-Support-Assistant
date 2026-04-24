from fastapi import APIRouter, HTTPException
from app.models import IngestResponse
from app.services.ingestion import ingest_documents
from app.services.retriever import get_document_count, reset_vectorstore

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion():
    """
    Trigger document ingestion pipeline.
    Loads all documents from the Documents/ directory,
    splits them into chunks, generates embeddings,
    and stores them in ChromaDB.
    """
    try:
        # Reset cached vectorstore so it reloads after ingestion
        reset_vectorstore()

        result = ingest_documents()
        return IngestResponse(**result)
    except Exception as e:
        print(f"[ERROR] Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/status")
async def get_ingestion_status():
    """
    Check the current status of the document store.
    Returns the number of document chunks stored in ChromaDB.
    """
    try:
        count = get_document_count()
        return {
            "status": "ready" if count > 0 else "empty",
            "total_chunks": count,
            "message": (
                f"{count} document chunks available in the knowledge base."
                if count > 0
                else "No documents ingested yet. Use POST /api/documents/ingest to add documents."
            ),
        }
    except Exception as e:
        print(f"[ERROR] Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
