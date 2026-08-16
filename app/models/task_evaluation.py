from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TaskEvaluation(Base):
    __tablename__ = "task_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    task_id = Column(
        Integer,
        ForeignKey(
            "agent_tasks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    result = Column(
        String(20),
        nullable=False,
    )

    checks = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    task = relationship(
        "AgentTask",
        back_populates="evaluations",
    )
