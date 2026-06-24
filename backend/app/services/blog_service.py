from app.graph.blog_graph import graph_app, State

from sqlalchemy.orm import Session
from app.db.repositories import BlogRepository
from app.db.dependencies import get_db

import json

class BlogService:

    @staticmethod
    def generate_blog(
        topic: str,
        as_of: str
    ):
        state = {
            "topic": topic.strip(),
            "mode": "",
            "needs_research": False,
            "queries": [],
            "evidence": [],
            "plan": None,
            "as_of": as_of,
            "recency_days": 7,
            "sections": [],
            "merged_md": "",
            "md_with_placeholders": "",
            "image_specs": [],
            "logs": [],
            "sub_logs": [],
            "final": "",
            }
        try :
            response : State = graph_app.invoke(state)

            blog = {
                    "topic": response["topic"],
                    "as_of": response["as_of"],
                    
                    "plan": response["plan"].model_dump()
                        if response.get("plan")
                        else None,

                    "tasks": [
                        task.model_dump()
                        for task in response.get("tasks", [])
                    ],

                    "evidence": [
                        evidence.model_dump()
                        for evidence in response.get("evidence", [])
                    ],

                    "images": response["image_specs"],

                    "markdown": response["final"],

                    "logs": response.get("logs", [])
                }
            
            saved_blog = BlogSaveService.save_blog(db=next(get_db()),blog_data=blog)

            return {
                    'type': 'completed',
                    'blog_id': saved_blog.id
                }

        except Exception as e:
            return {
                    'type': 'not_completed',
                    'error': e
                }
        
class BlogSaveService:

    @staticmethod
    def save_blog(
        db: Session,
        blog_data: dict
    ):
        return BlogRepository.create_blog(
            db=db,
            data=blog_data
        )
    
class BlogHistoryService:

    @staticmethod
    def get_all_blogs(
        db: Session
    ):
        blogs = BlogRepository.get_all_blogs(db)

        return [
            {
                "id": blog.id,
                "topic": blog.topic,
                "blog_title": blog.plan.get("blog_title", None),
                "created_at": blog.created_at
            }
            for blog in blogs
        ]

    @staticmethod
    def get_blog(
        db: Session,
        blog_id: int
    ):
        blog = BlogRepository.get_blog(
            db,
            blog_id
        )

        if not blog:
            return None

        return {
            "id": blog.id,

            "topic": blog.topic,

            "as_of": blog.as_of,

            "plan": blog.plan,

            "tasks": blog.tasks,

            "evidence": blog.evidence,

            "images": blog.images,

            "markdown": blog.markdown,

            "logs": blog.logs
        }
    
STEP_MAP = {
    "router": "Finding if research is needed",
    "research": "Gathering evidence",
    "orchestrator": "Planning blog structure",
    "worker": "Writing blog sections",
    "merge_content": "Combining sections",
    "decide_images": "Deciding images placeholders and Creating prompts",
    "generate_and_place_images": "Generating and Placing images",
    "final": "Finalizing the Blog",
}

class BlogStreamingService:

    @staticmethod
    async def event_generator(
        topic: str,
        as_of: str,):
        
        state = {
            "topic": topic.strip(),
            "mode": "",
            "needs_research": False,
            "queries": [],
            "evidence": [],
            "plan": None,
            "as_of": as_of,
            "recency_days": 7,
            "sections": [],
            "merged_md": "",
            "md_with_placeholders": "",
            "image_specs": [],
            "logs": [],
            "sub_logs": [],
            "final": "",
            }
        
        final_state: State = None
        worker_start = False 
        
        try :
            async for event in graph_app.astream_events(
                state,
                version="v2"
            ):
                event_name = event.get("name")

                if (
                    event["event"] == "on_chain_start"
                    and event_name in STEP_MAP
                ):
                    if event_name == "worker":
                        if worker_start:
                            continue

                        worker_start = True

                    if event_name == "merge_content":
                        if worker_start:
                            worker_start = False

                            data = json.dumps({
                            'type': 'step_completed',
                            'step': 'worker',
                            'label': STEP_MAP['worker']
                        })

                            yield (
                                f"data: {data}\n\n"
                            )

                    data = json.dumps({
                            'type': 'step_started',
                            'step': event_name,
                            'label': STEP_MAP[event_name]
                        })

                    yield (
                        f"data: {data}\n\n"
                    )

                elif (
                    event["event"] == "on_chain_end"
                    and event_name in STEP_MAP
                ):
                    if event_name == "worker":
                        continue

                    data = json.dumps({
                            'type': 'step_completed',
                            'step': event_name,
                            'label': STEP_MAP[event_name]
                        })

                    yield (
                        f"data: {data}\n\n"
                    )

                if (
                    event["event"] == "on_chain_end"
                    and event_name == "LangGraph"
                    and "input" not in event["data"]
                ):
                    
                    final_state: State = event["data"]["output"]

                    blog = {
                            "topic": final_state["topic"],
                            "as_of": str(final_state["as_of"]),
                            
                            "plan": final_state["plan"].model_dump()
                                if final_state.get("plan")
                                else None,

                            "tasks": [
                                task.model_dump()
                                for task in final_state.get("tasks", [])
                            ],

                            "evidence": [
                                evidence.model_dump()
                                for evidence in final_state.get("evidence", [])
                            ],

                            "images": final_state.get("image_specs", []),

                            "markdown": final_state["final"],

                            "logs": final_state.get("logs", [])
                            }
                    
                    saved_blog = BlogSaveService.save_blog(db=next(get_db()),blog_data=blog)

                    data = json.dumps({
                            'type': 'completed',
                            'blog_id': saved_blog.id
                        })
                    
                    yield (
                        f"data: {data}\n\n"
                    )

        except Exception as e:

            data = json.dumps({
                            'type': 'error',
                            'step': event_name,
                            'label': f"Unable to generate blog. Error: {e}"
                        })

            yield (
                f"data: {data}\n\n"
            )

    @staticmethod
    def delete_blog(
        db: Session,
        blog_id: int
    ):

        return BlogRepository.delete_blog(
            db,
            blog_id
        )