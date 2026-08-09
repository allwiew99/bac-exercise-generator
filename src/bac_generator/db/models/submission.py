from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from bac_generator.db.base import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    exercise_id: Mapped[int] = mapped_column(
        ForeignKey(
            "exercises.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    passed_tests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    total_tests: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )