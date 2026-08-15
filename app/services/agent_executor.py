from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.user import User


def execute_create_channel_and_send_message(
    db: Session,
    user: User,
    channel_name: str,
    message_content: str,
) -> Channel:
    existing_channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    if existing_channel:
        channel = existing_channel
    else:
        channel = Channel(
            name=channel_name,
            description=f"Channel created by agent task for {channel_name}",
            created_by=user.id,
        )

        db.add(channel)
        db.flush()

    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == user.id,
        ChannelMember.channel_id == channel.id,
    ).first()

    if not membership:
        membership = ChannelMember(
            user_id=user.id,
            channel_id=channel.id,
        )
        db.add(membership)
        db.flush()

    message = Message(
        content=message_content,
        user_id=user.id,
        channel_id=channel.id,
    )

    db.add(message)
    db.commit()
    db.refresh(channel)

    return channel
