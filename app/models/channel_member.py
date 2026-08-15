from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class ChannelMember(Base):
    __tablename__ = "channel_members"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    channel_id = Column(
        Integer,
        ForeignKey("channels.id"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="channel_memberships",
    )

    channel = relationship(
        "Channel",
        back_populates="memberships",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel_id",
            name="unique_user_channel",
        ),
    )
