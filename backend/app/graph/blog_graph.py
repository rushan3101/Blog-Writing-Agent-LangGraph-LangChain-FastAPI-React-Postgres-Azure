from __future__ import annotations

import operator
import os
from typing import TypedDict, List, Optional, Annotated
import time

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from app.graph.schemas import RouterDecision, EvidencePack,EvidenceItem, Plan, Task,TaskList
from app.graph.prompts import ROUTER_SYSTEM,RESEARCH_SYSTEM, PLAN_SYSTEM, TASK_SYSTEM, WORKER_SYSTEM
from app.graph.utils import _tavily_search
from app.graph.subgraph import reducer_subgraph,SubGraphState

from app.core.config import settings

load_dotenv()

os.environ["LANGCHAIN_PROJECT"] = "BLOG WRITING AGENT - REACT"


# -----------------------------
# 1) State
# -----------------------------
class State(TypedDict):
    topic: str

    # routing
    mode: str
    needs_research: bool
    queries: List[str]

    # research
    evidence: List[EvidenceItem]

    # orchestration
    plan: Optional[Plan]
    tasks: List[Task]

    # recency
    as_of: str
    recency_days: int

    # workers
    sections: Annotated[List[tuple[int, str]], operator.add]  # (task_id, section_md)

    # reducer/image
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]

    #Logs
    logs: Annotated[List[str], operator.add]
    sub_logs: Annotated[List[str], operator.add]

    final: str


# -----------------------------
# 2) LLM
# -----------------------------
router_llm = ChatGoogleGenerativeAI(model = settings.ROUTER)
research_llm = ChatGoogleGenerativeAI(model = settings.RESEARCH)
planner_llm = ChatGoogleGenerativeAI(model = settings.PLANNER)
task_llm = ChatGoogleGenerativeAI(model = settings.TASK, streaming=False)
worker_llm = ChatGoogleGenerativeAI(model = settings.WORKER)


# -----------------------------
# 3) Router
# -----------------------------
def router_node(state: State) -> dict:
    decider = router_llm.with_structured_output(RouterDecision)
    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {state['topic']}\nAs-of date: {state['as_of']}"),
        ]
    )

    if decision.mode == "open_book":
        recency_days = 7
    elif decision.mode == "hybrid":
        recency_days = 45
    else:
        recency_days = 3650

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
        "recency_days": recency_days,
        "logs": [f"Router completed | mode={decision.mode} | research={decision.needs_research}"]
    }

def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"


# -----------------------------
# 4) Research (Tavily)
# -----------------------------
def research_node(state: State) -> dict:
    queries = (state.get("queries") or [])[:10]
    raw: List[dict] = []
    for q in queries:
        raw.extend(_tavily_search(q, max_results=3))

    if not raw:
        return {"evidence": []}

    extractor = research_llm.with_structured_output(EvidencePack)
    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_SYSTEM),
            HumanMessage(
                content=(
                    f"As-of date: {state['as_of']}\n"
                    f"Recency days: {state['recency_days']}\n\n"
                    f"Raw results:\n{raw}"
                )
            ),
        ]
    )
    
    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e
    evidence = list(dedup.values())

    return {"evidence": evidence,
            "logs": [f"Research completed | Found {len(evidence)} Evidence"]}


# -----------------------------
# 5) Orchestrator (Plan)
# -----------------------------
def orchestrator_node(state: State) -> dict:

    mode = state.get("mode", "closed_book")
    evidence = state.get("evidence", [])

    forced_kind = "news_roundup" if mode == "open_book" else None

    # =====================================================
    # STEP 1: BLOG PLAN
    # =====================================================

    planner = planner_llm.with_structured_output(
        Plan,
        strict=True,
    )

    plan : Plan = planner.invoke(
        [
            SystemMessage(content=PLAN_SYSTEM),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n"
                    f"As-of: {state['as_of']}\n"
                    f"Recency Days: {state['recency_days']}\n"
                )
            ),
        ]
    )

    if forced_kind:
        plan.blog_kind = "news_roundup"

    # =====================================================
    # STEP 2: TASK GENERATION
    # =====================================================

    task_generator = task_llm.with_structured_output(
        TaskList,
        strict=True,
    )

    tasks_list: TaskList = task_generator.invoke(
        [
            SystemMessage(content=TASK_SYSTEM),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n\n"
                    f"Mode: {mode}\n"
                    f"As-of: {state['as_of']} (recency_days={state['recency_days']})\n"
                    f"{'Force blog_kind=news_roundup' if forced_kind else ''}\n\n"
                    f"Blog Plan:\n"
                    f"{plan.model_dump_json(indent=2)}\n\n"
                    f"Evidence:\n"
                    f"{[e.model_dump() for e in evidence][:10]}"
                )
            ),
        ]
    )

    tasks = tasks_list.tasks

    return {"plan": plan, "tasks": tasks,
            "logs": [f"Orchestrator completed | Created {len(tasks)} Tasks"]}


# -----------------------------
# 6) Fanout
# -----------------------------
def fanout(state: State):
    assert (state["plan"] is not None) and (state["tasks"] is not None)
    return [
        Send(
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "mode": state["mode"],
                "as_of": state["as_of"],
                "recency_days": state["recency_days"],
                "plan": state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
                "logs": state["logs"],
            },
        )
        for task in state["tasks"]
    ]


# -----------------------------
# 7) Worker
# -----------------------------
def worker_node(payload: dict) -> dict:
    task = Task(**payload["task"])
    plan = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]

    bullets_text = "\n- " + "\n- ".join(task.bullets)
    evidence_text = "\n".join(
        f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}"
        for e in evidence[:20]
    )

    section_md = worker_llm.invoke(
        [
            SystemMessage(content=WORKER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {plan.blog_title}\n"
                    f"Audience: {plan.audience}\n"
                    f"Tone: {plan.tone}\n"
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Constraints: {plan.constraints}\n"
                    f"Topic: {payload['topic']}\n"
                    f"Mode: {payload.get('mode')}\n"
                    f"As-of: {payload.get('as_of')} (recency_days={payload.get('recency_days')})\n\n"
                    f"Section title: {task.title}\n"
                    f"Goal: {task.goal}\n"
                    f"Target words: {task.target_words}\n"
                    f"Tags: {task.tags}\n"
                    f"requires_research: {task.requires_research}\n"
                    f"requires_citations: {task.requires_citations}\n"
                    f"requires_code: {task.requires_code}\n"
                    f"Bullets:{bullets_text}\n\n"
                    f"Evidence (ONLY cite these URLs):\n{evidence_text}\n"
                )
            ),
        ]
    ).content

    if isinstance(section_md, list):
        # gemini 3-1 flash lite returns list of dict [{"type": "text", "text": "..." }]
        section_md = section_md[0]["text"].strip()

    if isinstance(section_md, str):
        # gemini 2.5 flash lite returns string
        section_md = section_md.strip()

    return {"sections": [(task.id, section_md)],
            "logs": [f"Worker completed | Created section: {task.title}"] }


# ============================================================
# 8) Final Node
# ============================================================
def final_node(state: State) -> dict:
    time.sleep(3)
    return {
        "logs": state["sub_logs"] + [f"Final Blog Created"],
    }

# -----------------------------
# 9) Build Main graph
# -----------------------------
g = StateGraph(State)
g.add_node("router", router_node)
g.add_node("research", research_node)
g.add_node("orchestrator", orchestrator_node)
g.add_node("worker", worker_node)
g.add_node("reducer", reducer_subgraph)
g.add_node("final", final_node)

g.add_edge(START, "router")
g.add_conditional_edges("router", route_next, {"research": "research", "orchestrator": "orchestrator"})
g.add_edge("research", "orchestrator")

g.add_conditional_edges("orchestrator", fanout, ["worker"])
g.add_edge("worker", "reducer")
g.add_edge("reducer", "final")
g.add_edge("final", END)

app = g.compile()
graph_app = app
graph_app
        

