"""
Tool implementations for the Minicloud research agent.
Each tool is an async function decorated with @tool for LangGraph compatibility.
"""
import logging
import os

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

RAG_INGEST_URL = os.getenv("RAG_INGEST_URL", "http://rag-ingest.ai.svc.cluster.local:8001")


@tool
async def rag_search(query: str, collection: str = "") -> str:
    """Search the internal knowledge base for relevant documents and context.
    Use this for questions about company policies, regulations, stored documents,
    insurance products, financial instruments, or any information that may exist
    in the organisation's document repository."""
    try:
        payload: dict = {"query": query, "top_k": 5}
        if collection:
            payload["collection"] = collection
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{RAG_INGEST_URL}/query", json=payload)
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


@tool
async def web_search(query: str) -> str:
    """Search the public web using DuckDuckGo for current information, news,
    or facts not available in the internal knowledge base. Use for recent events,
    external regulatory updates, market data, or general knowledge questions."""
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


TOOLS = [rag_search, web_search]
