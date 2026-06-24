from app.db.models import Blog
from app.db.session import Base
from app.db.session import engine

Base.metadata.create_all(
    bind=engine
)

print("Tables created")