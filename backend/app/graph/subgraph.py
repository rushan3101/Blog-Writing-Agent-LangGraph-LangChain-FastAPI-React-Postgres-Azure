from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, List, Optional, Literal, Annotated
from pathlib import Path
import operator
from dotenv import load_dotenv

from app.graph.schemas import Plan, GlobalImagePlan
from app.graph.prompts import DECIDE_IMAGES_SYSTEM
from app.graph.utils import _safe_slug,_puter_generate_image_bytes
from app.core.config import settings
from app.services.blob_storage_service import BlobStorageService

load_dotenv()

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

image_decider_llm = ChatGoogleGenerativeAI(model = settings.IMAGE_DECIDER)

def merge_content(state: SubGraphState) -> dict:
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without plan.")
    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered_sections).strip()
    merged_md = f"# {plan.blog_title}\n\n{body}\n"
    
    return {"merged_md": merged_md, "sub_logs" : [f"Merged {len(state['sections'])} sections."] }  

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

def generate_and_place_images(state: SubGraphState) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    # If no images requested, just return markdown as-is
    if not image_specs:
        return {"final": md, "image_specs": []}

    blob_service = BlobStorageService()
    blog_slug = _safe_slug(plan.blog_title)

    updated_specs = []

    for spec in image_specs:
        placeholder = spec["placeholder"]
        img_filename = spec["filename"]

        # blob path inside container
        blob_path = f"{blog_slug}/{img_filename}"

        try:
            img_bytes = _puter_generate_image_bytes(spec["prompt"])

            image_url = blob_service.upload_image(
                blob_path=blob_path,
                data=img_bytes,
                content_type="image/png",
            )

            spec["image_url"] = image_url
            spec["blob_path"] = blob_path

            img_md = (
                f'![{spec["alt"]}]({image_url})\n'
                f'*{spec["caption"]}*'
            )

            md = md.replace(placeholder, img_md)

        except Exception as e:
            prompt_block = (
                f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                f"> **Alt:** {spec.get('alt','')}\n>\n"
                f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                f"> **Error:** {e}\n"
            )
            md = md.replace(placeholder, prompt_block)

        updated_specs.append(spec)

    return {
        "final": md,
        "image_specs": updated_specs,
        "sub_logs" : [f"Generated {len(updated_specs)} images."],
    }
   
   
reducer_graph = StateGraph(SubGraphState)
reducer_graph.add_node("merge_content", merge_content)
reducer_graph.add_node("decide_images", decide_images)
reducer_graph.add_node("generate_and_place_images", generate_and_place_images)
reducer_graph.add_edge(START, "merge_content")
reducer_graph.add_edge("merge_content", "decide_images")
reducer_graph.add_edge("decide_images", "generate_and_place_images")
reducer_graph.add_edge("generate_and_place_images", END)
reducer_subgraph = reducer_graph.compile()
reducer_subgraph