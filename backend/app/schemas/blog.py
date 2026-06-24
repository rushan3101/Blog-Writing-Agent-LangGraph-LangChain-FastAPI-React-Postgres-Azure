from pydantic import BaseModel
from datetime import date
from typing import List
from app.graph.blog_graph import (
    Plan,
    Task,
    EvidenceItem
)

class GenerateBlogRequest(BaseModel):
    topic: str
    as_of: date

class ImageResponse(BaseModel):
    placeholder: str
    filename: str

    alt: str
    caption: str

    prompt: str
    size: str
    quality: str

    image_url: str | None = None
    blob_path: str | None = None

class BlogResponse(BaseModel):
    topic: str
    as_of: date
    plan: Plan | None
    tasks: List[Task]
    evidence: List[EvidenceItem]
    markdown: str
    images: List[ImageResponse]
    logs: List[str]

class SaveBlogRequest(BaseModel):
    topic: str

    as_of: str

    plan: Plan | None

    tasks: list[Task]

    evidence: list[EvidenceItem] | None

    images: List[ImageResponse] | None

    markdown: str

    logs: list[str]


