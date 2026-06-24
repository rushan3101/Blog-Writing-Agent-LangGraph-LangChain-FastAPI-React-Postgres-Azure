from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import StreamingResponse
from app.schemas.blog import (
    GenerateBlogRequest,
    BlogResponse,
    SaveBlogRequest
)
from app.services.blog_service import BlogService, BlogSaveService, BlogHistoryService, BlogStreamingService

from sqlalchemy.orm import Session
from app.db.dependencies import get_db

router = APIRouter(
    prefix="/blogs",
    tags=["Blogs"]
)

@router.post("/generate")
async def generate_blog(
    request: GenerateBlogRequest
):

    result = BlogService.generate_blog(
        topic=request.topic,
        as_of=request.as_of
    )

    return result

@router.post("/save")
async def save_blog(
    request: SaveBlogRequest,
    db: Session = Depends(get_db)
):
    blog = BlogSaveService.save_blog(
        db=db,
        blog_data=request.model_dump()
    )

    return {
        "message": "Blog saved",
        "id": blog.id
    }

@router.get("/")
async def get_blogs(
    db: Session = Depends(get_db)
):
    blogs = BlogHistoryService.get_all_blogs(db)

    return blogs

@router.get("/{blog_id}")
async def get_blog(
    blog_id: int,
    db: Session = Depends(get_db)
):
    blog = BlogHistoryService.get_blog(
        db,
        blog_id
    )

    return blog

@router.post("/generate-stream")
async def generate_blog_stream(
    request: GenerateBlogRequest
):

    return StreamingResponse(
        BlogStreamingService.event_generator(
            request.topic,
            request.as_of
        ),
        media_type="text/event-stream"
    )

@router.delete("/{blog_id}")
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db)
):

    success = BlogStreamingService.delete_blog(
        db,
        blog_id
    )

    return {
        "success": success
    }

