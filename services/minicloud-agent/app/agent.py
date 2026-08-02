"""
ReAct agent using LangGraph's prebuilt create_react_agent.
All model calls route through LiteLLM so Presidio, LlamaGuard, Langfuse tracing,
rate limiting, and cost tracking apply to every tool-calling step.
"""
import logging
import os

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .tools import TOOLS

logger = logging.getLogger(__name__)

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm.ai.svc.cluster.local:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-agent-internal")
DEFAULT_MODEL = os.getenv("AGENT_DEFAULT_MODEL", "mistral-small")
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))

SYSTEM_PROMPT = (
    "You are a research assistant with access to two tools: "
    "rag_search (internal knowledge base) and web_search (public web via DuckDuckGo). "
    "Always search the internal knowledge base first for proprietary or domain-specific "
    "information. Use web_search only when the knowledge base returns no useful results "
    "or when the user explicitly asks about current events. "
    "Cite your sources in the final answer using the [N] references from tool outputs."
)


def _build_agent(model_name: str):
    llm = ChatOpenAI(
        model=model_name,
        base_url=f"{LITELLM_BASE_URL}/v1",
        api_key=LITELLM_API_KEY,
    )
    return create_react_agent(llm, TOOLS)


def _to_langchain_messages(openai_messages: list[dict]):
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in openai_messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        # system messages from the caller are dropped — the agent has its own
    return lc_messages


async def run(messages: list[dict], model_name: str = DEFAULT_MODEL) -> str:
    """Run the agent to completion and return the final answer as a string."""
    agent = _build_agent(model_name)
    lc_messages = _to_langchain_messages(messages)

    config = {"recursion_limit": MAX_ITERATIONS * 2 + 1}
    result = await agent.ainvoke({"messages": lc_messages}, config=config)

    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content:
            return str(msg.content)

    return "Agent completed without producing a final answer."
