from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    channels = relationship(
        "Channel",
        back_populates="creator",
        cascade="all, delete-orphan",
    )

    channel_memberships = relationship(
        "ChannelMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    agent_tasks = relationship(
        "AgentTask",
        back_populates="user",
        cascade="all, delete-orphan",
    )
