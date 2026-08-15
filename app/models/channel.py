from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    creator = relationship(
        "User",
        back_populates="channels",
    )

    memberships = relationship(
        "ChannelMember",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    messages = relationship(
        "Message",
        back_populates="channel",
        cascade="all, delete-orphan",
    )
