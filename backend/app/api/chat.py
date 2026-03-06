from fastapi import APIRouter, HTTPException
from app.services.rag import RAGService
from app.services.token_logger import TokenLogger
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
rag_service = RAGService()
token_logger = TokenLogger()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    import traceback
    try:
        result = await rag_service.answer(
            question=request.question,
            history=request.history,
            doc_filter=request.doc_filter
        )
        token_logger.log(result["token_usage"])
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Retrieve conversation history for a session."""
    history = await rag_service.get_history(session_id)
    return {"session_id": session_id, "history": history}

@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    await rag_service.clear_history(session_id)
    return {"message": "History cleared"}
