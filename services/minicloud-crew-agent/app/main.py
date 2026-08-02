"""
Minicloud Crew Agent Runtime — OpenAI-compatible FastAPI service.

Exposes a three-agent CrewAI crew (Researcher → Analyst → Compliance Checker)
as a drop-in chat model. Register as `model: deep-research-agent` in LiteLLM.

Architecture:
  Client → LiteLLM proxy → minicloud-crew-agent:8081 → CrewAI Crew
                                                        ├── Researcher   (mistral-small + rag + web)
                                                        ├── Analyst      (mistral-large, synthesis)
                                                        └── Compliance   (mistral-large + rag, validation)
"""
import json
import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .crew import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minicloud Crew Agent Runtime",
    version="1.0.0",
    docs_url="/docs",
)

AGENT_MODEL_IDS = ["deep-research-agent"]


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "deep-research-agent"
    messages: list[Message]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


def _extract_question(messages: list[Message]) -> str:
    for m in reversed(messages):
        if m.role == "user" and m.content:
            return m.content
    return ""


@app.get("/health")
async def health():
    return {"status": "ok", "service": "minicloud-crew-agent"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 1700000000,
                "owned_by": "minicloud",
            }
            for model_id in AGENT_MODEL_IDS
        ],
    }


async def _sse_stream(request_id: str, model: str, content: str):
    chunk_size = 40
    for i in range(0, len(content), chunk_size):
        piece = content[i : i + chunk_size]
        data = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {"index": 0, "delta": {"content": piece}, "finish_reason": None}
            ],
        }
        yield f"data: {json.dumps(data)}\n\n"

    done_data = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(done_data)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    request_id = f"chatcmpl-crew-{uuid.uuid4().hex[:8]}"
    question = _extract_question(request.messages)

    logger.info(
        "Crew request id=%s model=%s messages=%d question=%.80s",
        request_id,
        request.model,
        len(request.messages),
        question,
    )

    content = await run(question)

    if request.stream:
        return StreamingResponse(
            _sse_stream(request_id, request.model, content),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
