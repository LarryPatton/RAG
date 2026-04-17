from fastapi import APIRouter
from pydantic import BaseModel

from api.services.agent_service import agent_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    llm_mode: str = "ollama"


class ChatResponse(BaseModel):
    reply: str
    text: str
    structured_data: dict | None = None
    stage: str


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = agent_service.chat(
        message=req.message,
        history=req.history,
        llm_mode=req.llm_mode,
    )
    return ChatResponse(**result)
