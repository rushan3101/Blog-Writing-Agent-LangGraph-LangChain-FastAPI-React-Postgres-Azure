from sqlalchemy.orm import Session

from app.db.models import Blog

from app.services.blob_storage_service import BlobStorageService

class BlogRepository:

    @staticmethod
    def create_blog(
        db: Session,
        data: dict
    ):
        blog = Blog(**data)

        db.add(blog)

        db.commit()

        db.refresh(blog)

        return blog
    
    @staticmethod
    def get_all_blogs(
        db: Session
    ):
        return (
            db.query(Blog)
            .order_by(
                Blog.created_at.desc()
            )
            .all()
        )
    
    @staticmethod
    def get_blog(
        db: Session,
        blog_id: int
    ):
        return db.get(
            Blog,
            blog_id
        )
    
    @staticmethod
    def delete_blog(
        db: Session,
        blog_id: int
    ):

        blog = db.get(
            Blog,
            blog_id
        )

        if not blog:
            return {"message": f"Blog {blog_id} not found"}
        
        blob_service = BlobStorageService()

        images = blog.images or []

        for image in images:
            blob_path = image.get("blob_path", None)
            if blob_path:
                try:
                    blob_service.delete_blob(blob_path)
                except Exception as e:
                    print(f"Failed to delete blob {blob_path}: {e}")

        db.delete(blog)

        db.commit()

        return {"message": f"Blog {blog_id} deleted successfully"}