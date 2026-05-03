"""
Chat Router — RAG API Endpoint
POST /api/chat — Send message to Smart Energy RAG API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.api_client import RAGClient

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Proxy request to RAG API
    Supports multiple response formats from HuggingFace APIs
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = RAGClient.chat(req.message)
    
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    
    # Extract response based on various HF API response formats
    response_text = (
        result.get("response") 
        or result.get("message") 
        or result.get("generated_text")
        or (result[0]["generated_text"] if isinstance(result, list) and len(result) > 0 else None)
        or str(result)
    )
    
    return ChatResponse(response=response_text)
