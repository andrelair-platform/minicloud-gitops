"""
Three-agent CrewAI crew: Researcher → Analyst → Compliance Checker.

Each request creates a fresh Crew with dynamically-scoped tasks.
Agents are module-level singletons (stateless between requests).
The crew runs via run_in_executor so FastAPI's event loop is never blocked.
"""
import asyncio
import logging
import os

from crewai import Agent, Crew, LLM, Process, Task

from .tools import RagSearchTool, WebSearchTool

logger = logging.getLogger(__name__)

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm.ai.svc.cluster.local:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "none")
SMALL_MODEL = os.getenv("CREW_SMALL_MODEL", "mistral-small")
LARGE_MODEL = os.getenv("CREW_LARGE_MODEL", "mistral-large")
MAX_ITER = int(os.getenv("CREW_MAX_ITER", "8"))


def _llm(model: str) -> LLM:
    # "openai/<model>" tells litellm to use OpenAI-compatible format against
    # the proxy's base_url, which maps the virtual model name to the real provider.
    return LLM(
        model=f"openai/{model}",
        base_url=f"{LITELLM_BASE_URL}/v1",
        api_key=LITELLM_API_KEY,
        temperature=0.1,
        max_retries=2,
    )


_rag = RagSearchTool()
_web = WebSearchTool()

researcher = Agent(
    role="Research Specialist",
    goal=(
        "Find accurate and comprehensive information to answer the user's question. "
        "Prefer internal knowledge base results over web results when both are available."
    ),
    backstory=(
        "You are a meticulous researcher for a financial and insurance advisory platform. "
        "You have access to internal regulatory documents and the public web. "
        "You always cite your sources with numbered references [1], [2], etc."
    ),
    tools=[_rag, _web],
    llm=_llm(SMALL_MODEL),
    max_iter=MAX_ITER,
    verbose=False,
)

analyst = Agent(
    role="Financial Analyst",
    goal=(
        "Synthesise the research findings into a clear, structured, and actionable answer. "
        "Preserve every source citation [N] from the research verbatim."
    ),
    backstory=(
        "You are a senior financial analyst specialising in insurance, asset management, "
        "and financial regulation (Solvency II, MiFID II, ACPR, AMF). "
        "You turn raw research into concise, well-structured explanations "
        "that professionals can act on immediately."
    ),
    tools=[],
    llm=_llm(LARGE_MODEL),
    max_iter=4,
    verbose=False,
)

compliance_checker = Agent(
    role="Compliance Validator",
    goal=(
        "Verify that every regulatory claim in the analysis is accurate and sourced. "
        "Use rag_search to cross-check specific references. "
        "Deliver the final validated answer ready for the user."
    ),
    backstory=(
        "You are a regulatory compliance expert specialising in ACPR, AMF, "
        "Solvency II, MiFID II, and GDPR. You never allow an unsupported regulatory "
        "claim to reach the user. You correct errors and note any changes made."
    ),
    tools=[_rag],
    llm=_llm(LARGE_MODEL),
    max_iter=MAX_ITER,
    verbose=False,
)


def _build_crew(question: str) -> tuple[Crew, dict]:
    """Return a fresh Crew and the inputs dict for kickoff."""
    research_task = Task(
        description=(
            "Research the following question using your tools.\n"
            "1. Search the internal knowledge base first with rag_search.\n"
            "2. If results are insufficient or the question requires current data, "
            "use web_search.\n"
            "3. Compile all findings and cite every source as [1], [2], etc.\n\n"
            "Question: {question}"
        ),
        expected_output=(
            "Comprehensive research findings with all sources cited as [N]. "
            "Include relevant text excerpts."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Using the research findings, write a clear structured answer.\n"
            "Structure: executive summary, key facts, regulatory context, "
            "practical implications.\n"
            "Preserve all [N] citations exactly as they appear in the research.\n\n"
            "Question: {question}"
        ),
        expected_output=(
            "Structured answer (200–400 words) with all claims cited using [N] notation."
        ),
        agent=analyst,
        context=[research_task],
    )

    compliance_task = Task(
        description=(
            "Review the analyst's answer for regulatory accuracy.\n"
            "1. Identify every regulatory reference (ACPR, AMF, Solvency II, "
            "MiFID II, GDPR, etc.).\n"
            "2. Use rag_search to verify any claim you are uncertain about.\n"
            "3. Correct errors and return the complete validated answer.\n"
            "4. If you made corrections, add a brief 'Compliance note:' at the end.\n\n"
            "Question: {question}"
        ),
        expected_output=(
            "The complete, validated answer with all regulatory claims verified. "
            "Optionally followed by a 'Compliance note:' if corrections were needed."
        ),
        agent=compliance_checker,
        context=[research_task, analysis_task],
    )

    crew = Crew(
        agents=[researcher, analyst, compliance_checker],
        tasks=[research_task, analysis_task, compliance_task],
        process=Process.sequential,
        verbose=False,
    )
    return crew, {"question": question}


async def run(question: str) -> str:
    """Run the three-agent crew and return the compliance-validated answer."""
    crew, inputs = _build_crew(question)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None, lambda: crew.kickoff(inputs=inputs)
    )
    return str(result)
