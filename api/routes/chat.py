import asyncio
import json
import logging
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.services.agent_service import agent_service

router = APIRouter()
logger = logging.getLogger(__name__)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(max_length=2000)
    history: list[HistoryMessage] = Field(default=[], max_length=50)
    llm_mode: str = "ollama"
    user_decisions: dict[str, str] | None = None


class ChatResponse(BaseModel):
    reply: str
    text: str
    structured_data: dict | None = None
    stage: str
    thinking_steps: list[dict] = []
    task_plan: dict | None = None


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    result = await asyncio.to_thread(
        agent_service.chat,
        message=req.message,
        history=history_dicts,
        llm_mode=req.llm_mode,
        user_decisions=req.user_decisions or {},
    )
    return ChatResponse(**result)


@router.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE streaming endpoint. Yields events as `data: {json}\n\n`."""
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]

    async def generate():
        done_sent = False
        try:
            async for event in agent_service.stream_chat(
                message=req.message,
                history=history_dicts,
                llm_mode=req.llm_mode,
                user_decisions=req.user_decisions or {},
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "done":
                    done_sent = True
        except Exception as e:
            logger.exception("Error during stream_chat")
            yield f"data: {json.dumps({'type': 'error', 'message': '服务处理出错，请重试'})}\n\n"
        finally:
            if not done_sent:
                yield f"data: {json.dumps({'type': 'done', 'clean_text': ''})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
