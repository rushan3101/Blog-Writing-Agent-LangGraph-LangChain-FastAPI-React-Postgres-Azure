from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text
)

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.session import Base

class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    topic: Mapped[str] = mapped_column(
        String(500)
    )

    as_of: Mapped[str] = mapped_column(
        String(15)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    plan: Mapped[dict] = mapped_column(
        JSONB
    )

    tasks: Mapped[list] = mapped_column(
        JSONB
    )

    evidence: Mapped[list] = mapped_column(
        JSONB
    )

    images: Mapped[list] = mapped_column(
        JSONB
    )

    markdown: Mapped[str] = mapped_column(
        Text
    )

    logs: Mapped[list] = mapped_column(
        JSONB
    )