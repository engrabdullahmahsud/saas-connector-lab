from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)

    instruction = Column(Text, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
