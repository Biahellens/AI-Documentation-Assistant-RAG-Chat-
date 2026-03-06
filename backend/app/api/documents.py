from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ingestion import IngestionService
from app.models.schemas import DocumentUploadResponse, DocumentListResponse

router = APIRouter()
ingestion_service = IngestionService()

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a PDF or Markdown file."""
    allowed_types = ["application/pdf", "text/markdown", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not supported: {file.content_type}")

    content = await file.read()
    result = await ingestion_service.ingest(
        filename=file.filename,
        content=content,
        content_type=file.content_type
    )
    return result

@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """List all indexed documents."""
    docs = await ingestion_service.list_documents()
    return {"documents": docs}

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document from the index."""
    await ingestion_service.delete_document(doc_id)
    return {"message": f"Document {doc_id} deleted"}
