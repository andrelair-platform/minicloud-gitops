"""
Minicloud Agent Runtime — OpenAI-compatible FastAPI service.

Exposes a LangGraph ReAct agent as a drop-in replacement for any chat model.
Register as `model: research-agent` in LiteLLM config to make it available
in Open WebUI and any OpenAI-compatible client.

Architecture:
  Client → LiteLLM proxy → minicloud-agent:8080 → LangGraph agent
                                                  ├── rag_search → rag-ingest:8001
                                                  ├── web_search → DuckDuckGo
                                                  └── model calls → LiteLLM (mistral-small)
"""
import json
import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import run, DEFAULT_MODEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minicloud Agent Runtime",
    version="1.0.0",
    docs_url="/docs",
)

AGENT_MODEL_IDS = ["research-agent"]

MODEL_TO_LLM = {
    "research-agent": DEFAULT_MODEL,
}


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "research-agent"
    messages: list[Message]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "minicloud-agent"}


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
    """Yield the final agent response as OpenAI-compatible SSE chunks."""
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
    request_id = f"chatcmpl-agent-{uuid.uuid4().hex[:8]}"
    llm_model = MODEL_TO_LLM.get(request.model, DEFAULT_MODEL)
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    logger.info(
        "Agent request id=%s model=%s llm=%s messages=%d",
        request_id, request.model, llm_model, len(messages),
    )

    content = await run(messages, model_name=llm_model)

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
