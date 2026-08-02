"""
CrewAI tool definitions for the minicloud-crew-agent.
BaseTool subclasses with synchronous _run methods — CrewAI calls these in a
thread executor internally when running an async crew kickoff.
"""
import logging
import os

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class _RagSearchInput(BaseModel):
    query: str = Field(description="Search query for the knowledge base")
    collection: str = Field(default="", description="Optional collection UUID to restrict the search")


class RagSearchTool(BaseTool):
    name: str = "rag_search"
    description: str = (
        "Search the internal knowledge base for regulatory documents, policy texts, "
        "financial instruments, insurance products, and company procedures. "
        "Always try this before searching the web."
    )
    args_schema: type[BaseModel] = _RagSearchInput

    def _run(self, query: str, collection: str = "") -> str:
        rag_url = os.getenv("RAG_INGEST_URL", "http://rag-ingest.ai.svc.cluster.local:8001")
        try:
            payload: dict = {"query": query, "top_k": 5}
            if collection:
                payload["collection"] = collection
            response = httpx.post(f"{rag_url}/query", json=payload, timeout=10.0)
            response.raise_for_status()
            chunks = response.json().get("results", [])
            if not chunks:
                return "No relevant documents found in the knowledge base for this query."
            parts = []
            for i, chunk in enumerate(chunks[:5], 1):
                source = chunk.get("source", "Unknown")
                text = (chunk.get("text") or chunk.get("content") or "")[:600]
                parts.append(f"[{i}] Source: {source}\n{text}")
            return "\n\n".join(parts)
        except Exception as exc:
            logger.warning("rag_search error: %s", exc)
            return f"Knowledge base search unavailable: {exc}"


class _WebSearchInput(BaseModel):
    query: str = Field(description="Search query for the public web")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the public web for current information, news, regulatory updates, "
        "market data, or general knowledge not available in the internal knowledge base."
    )
    args_schema: type[BaseModel] = _WebSearchInput

    def _run(self, query: str) -> str:
        try:
            from ddgs import DDGS
            results = list(DDGS().text(query, max_results=5))
            if not results:
                return "No web results found for this query."
            parts = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                url = r.get("href", "")
                snippet = (r.get("body") or "")[:400]
                parts.append(f"[{i}] {title}\n{url}\n{snippet}")
            return "\n\n".join(parts)
        except Exception as exc:
            logger.warning("web_search error: %s", exc)
            return f"Web search unavailable: {exc}"
