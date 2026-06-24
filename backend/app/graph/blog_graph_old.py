from __future__ import annotations

import operator
import os
import re
from pathlib import Path
from typing import TypedDict, List, Optional, Literal, Annotated
import time

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

import requests
import base64

load_dotenv()

os.environ["LANGCHAIN_PROJECT"] = "BLOG WRITING AGENT - REACT"

# -----------------------------
# 1) Schemas
# -----------------------------
class Task(BaseModel):
    id: int = Field(..., description="Unique identifier for the task.")
    title: str = Field(..., description="Title of the task.")
    goal: str = Field(..., description="One sentence describing what the reader should do/understand.")
    bullets: List[str] = Field(..., min_length=3, max_length=6)
    target_words: int = Field(..., description="Target words (120–550).")

    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str = Field(..., description="Title of the blog post.")
    audience: str = Field(..., description="Target audience.")
    tone: str = Field(..., description="Blog tone.")
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)

class TaskList(BaseModel):
    tasks: List[Task] = Field(..., min_length=4, max_length=5, description="List of Tasks for the blog post.")


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None  # ISO "YYYY-MM-DD" preferred
    snippet: Optional[str] = None
    source: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    reason: str
    queries: List[str] = Field(default_factory=list, min_length=5, max_length=6)
    max_results_per_query: int = Field(5)


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


# ---- Image planning schema (ported from your image flow) ----
class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. qkv_flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)

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

class SubGraphState(TypedDict):
    topic: str

    # orchestration
    plan: Optional[Plan]

    # workers
    sections: Annotated[List[tuple[int, str]], operator.add]  # (task_id, section_md)

    # reducer/image
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]

    #Logs
    sub_logs: Annotated[List[str], operator.add]

    final: str


# -----------------------------
# 2) LLM
# -----------------------------
router_llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")
research_llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")
planner_llm = ChatGoogleGenerativeAI(model = "gemini-3-flash-preview")
task_llm = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",streaming=False)
worker_llm = ChatGoogleGenerativeAI(model = "gemini-3.1-flash-lite")
image_decider_llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


# -----------------------------
# 3) Router
# -----------------------------
ROUTER_SYSTEM = """You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.

Modes:
- closed_book (needs_research=false): evergreen concepts.
- hybrid (needs_research=true): evergreen + needs up-to-date examples/tools/models.
- open_book (needs_research=true): volatile weekly/news/"latest"/pricing/policy.

If needs_research=true:
- Output 5-6 high-signal, scoped queries.
- For open_book weekly roundup, include queries reflecting last 7 days.
"""

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
def _tavily_search(query: str, max_results) -> List[dict]:
    if not os.getenv("TAVILY_API_KEY"):
        return []
    try:
        from langchain_tavily import TavilySearch  
        tool = TavilySearch(tavily_api_key=os.getenv("TAVILY_API_KEY"), max_results=max_results)
        results = tool.invoke({"query": query})["results"]
        out = []
        for r in results or []:
            out.append(
                {
                    "title": r.get("title") or "",
                    "url": r.get("url") or "",
                    "snippet": r.get("content") or r.get("snippet") or "",
                    "published_at": r.get("published_date") or r.get("published_at"),
                    "source": r.get("source"),
                }
            )
        return out
    except Exception as e:
        print(e)
        return []

RESEARCH_SYSTEM = """You are a research synthesizer.

Given raw web search results, produce EvidenceItem objects.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources.
- Normalize published_at to ISO YYYY-MM-DD if reliably inferable; else null (do NOT guess).
- Keep snippets short.
- Deduplicate by URL.
"""

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
PLAN_SYSTEM = """
You are a senior technical blog strategist.

Your job is ONLY to determine the overall blog strategy.

Return a valid BlogPlan object.

Fields:

- blog_title
- audience
- tone
- blog_kind
- constraints

Rules:

- audience should be a short reader description.
- tone should be a short style description.
- constraints should contain practical writing constraints or [].
- blog_kind must be one of:
  - explainer
  - tutorial
  - news_roundup
  - comparison
  - system_design

Mode guidance:

- open_book:
    prefer news_roundup when discussing recent developments.
- closed_book:
    choose the most appropriate type.

Keep decisions conservative and realistic.
Do not hallucinate facts.
Return only structured data.
"""

TASK_SYSTEM = """
You are a senior technical editor.

Your job is to convert a blog plan into an actionable writing outline.

Return a TaskList object.

Rules:

- Generate exactly 5 tasks.
- Tasks must be ordered logically.
- Each task should correspond to one major section of the blog.
- Every task must have:

    - id
    - title
    - goal
    - bullets
    - target_words
    - tags
    - requires_research
    - requires_citations
    - requires_code

Bullets:

- 3 to 6 bullets
- concise
- actionable
- no paragraphs

target_words:

- integer
- between 150 and 450

Research Rules:

- If evidence is available and task relies on factual claims:
    requires_research=True

- If evidence should be cited:
    requires_citations=True

- If examples can be explained from general knowledge:
    requires_research=False

Code Rules:

- requires_code=True only when code examples genuinely help.

Return only structured data.
"""

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
WORKER_SYSTEM = """You are a senior technical writer and developer advocate.
Write ONE section of a technical blog post in Markdown.

Constraints:
- Cover ALL bullets in order.
- Target words ±15%.
- Output only section markdown starting with "## <Section Title>".

Scope guard:
- If blog_kind=="news_roundup", do NOT drift into tutorials (scraping/RSS/how to fetch).
  Focus on events + implications.

Grounding:
- If mode=="open_book": do not introduce any specific event/company/model/funding/policy claim unless supported by provided Evidence URLs.
  For each supported claim, attach a Markdown link ([Source](URL)).
  If unsupported, write "Not found in provided sources."
- If requires_citations==true (hybrid tasks): cite Evidence URLs for external claims.

Code:
- If requires_code==true, include at least one minimal snippet.
"""

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
# 8) Reducer With Images (subgraph)
#    merge_content -> decide_images -> generate_and_place_images
# ============================================================
def merge_content(state: SubGraphState) -> dict:
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without plan.")
    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    merged_md = f"# {plan.blog_title}\n\n{body}\n"
    
    return {"merged_md": merged_md, "sub_logs" : [f"Merged {len(state['sections'])} sections."] }  


DECIDE_IMAGES_SYSTEM = """You are an expert technical editor.
Decide if images/diagrams are needed for THIS blog.

Rules:
- Max 3 images total.
- Each image must materially improve understanding (diagram/flow/table-like visual).
- Insert placeholders exactly: [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]].
- If no images needed: md_with_placeholders must equal input and images=[].
- Avoid decorative images; prefer technical diagrams with short labels.
Return strictly GlobalImagePlan.
"""

def decide_images(state: SubGraphState) -> dict:
    
    merged_md = state["merged_md"]
    plan = state["plan"]
    assert plan is not None

    img_planner = image_decider_llm.with_structured_output(GlobalImagePlan)
    image_plan: GlobalImagePlan = img_planner.invoke(
        [
            SystemMessage(content=DECIDE_IMAGES_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Topic: {state['topic']}\n\n"
                    "Insert placeholders + propose image prompts.\n\n"
                    f"{merged_md}"
                )
            ),
        ]
    )

    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
        "sub_logs" : [f"Decided Placeholders and Created prompts for {len(image_plan.images)} images."],
    }


def _puter_generate_image_bytes(prompt: str) -> bytes:
    """
    Generate image using Puter and return raw image bytes.

    Requires:
        PUTER_TOKEN in environment

    Returns:
        bytes
    """

    token = os.getenv("PUTER_TOKEN")

    if not token:
        raise RuntimeError("PUTER_TOKEN is not set.")

    payload = {
        "interface": "puter-image-generation",
        "driver": "ai-image",
        "method": "generate",
        "test_mode": False,
        "args": {
            "model": "gpt-image-1-mini",
            "prompt": prompt,
        },
        "auth_token": token,
    }

    response = requests.post(
        "https://api.puter.com/drivers/call",
        json=payload,
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    if "result" not in result:
        raise RuntimeError(f"Unexpected response: {result}")

    data_uri = result["result"]

    if not data_uri.startswith("data:image"):
        raise RuntimeError(f"Expected image data URI, got: {data_uri[:100]}")

    try:
        _, image_b64 = data_uri.split(",", 1)
        return base64.b64decode(image_b64)
    except Exception as e:
        raise RuntimeError(f"Failed to decode image response: {e}")

def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"

def generate_and_place_images(state: SubGraphState) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    # If no images requested, just write merged markdown
    if not image_specs:
        return {"final": md}

    folder_name = _safe_slug(plan.blog_title)
    images_dir = Path("images", folder_name)
    images_dir.mkdir(parents=True,exist_ok=True)

    for spec in image_specs:
        placeholder = spec["placeholder"]
        img_filename = spec["filename"]
        out_path = images_dir / img_filename

        # generate only if needed
        if not out_path.exists():
            try:
                img_bytes = _puter_generate_image_bytes(spec["prompt"])
                out_path.write_bytes(img_bytes)
                            
            except Exception as e:
                # graceful fallback: keep doc usable
                prompt_block = (
                    f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                    f"> **Alt:** {spec.get('alt','')}\n>\n"
                    f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                    f"> **Error:** {e}\n"
                )
                md = md.replace(placeholder, prompt_block)
                continue

        spec["image_url"] = f"http://localhost:8000/blogs/images/{folder_name}/{img_filename}"        
        img_md = f"![{spec['alt']}]({spec['image_url']})\n*{spec['caption']}*"
        md = md.replace(placeholder, img_md)

    return {"final": md, "image_specs": image_specs,
            "sub_logs": [f"Generated {len(image_specs)} images."]}


def final_node(state: State) -> dict:
    time.sleep(3)
    return {
        "logs": state["sub_logs"] + [f"Final Blog Created"],
    }

# -----------------------------
# 9) Build Reducer Subgraph
# -----------------------------
reducer_graph = StateGraph(SubGraphState)
reducer_graph.add_node("merge_content", merge_content)
reducer_graph.add_node("decide_images", decide_images)
reducer_graph.add_node("generate_and_place_images", generate_and_place_images)
reducer_graph.add_edge(START, "merge_content")
reducer_graph.add_edge("merge_content", "decide_images")
reducer_graph.add_edge("decide_images", "generate_and_place_images")
reducer_graph.add_edge("generate_and_place_images", END)
reducer_subgraph = reducer_graph.compile()

# -----------------------------
# 10) Build Main graph
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
        

