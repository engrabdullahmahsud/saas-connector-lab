import re

from sqlalchemy.orm import Session

from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.user import User


def execute_create_channel(
    db: Session,
    user: User,
    channel_name: str,
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
        db.add(
            ChannelMember(
                user_id=user.id,
                channel_id=channel.id,
            )
        )
        db.flush()

    return channel


def execute_create_channel_and_send_message(
    db: Session,
    user: User,
    channel_name: str,
    message_content: str,
) -> Channel:
    channel = execute_create_channel(
        db=db,
        user=user,
        channel_name=channel_name,
    )

    message = Message(
        content=message_content,
        user_id=user.id,
        channel_id=channel.id,
    )

    db.add(message)
    db.commit()
    db.refresh(channel)

    return channel


def execute_agent_task(
    db: Session,
    task: AgentTask,
    user: User,
) -> AgentTask:
    instruction = task.instruction.strip()

    message_match = re.fullmatch(
        r"Create a channel called (.+?) and send the message (.+)",
        instruction,
        re.IGNORECASE,
    )

    if message_match:
        channel_name = message_match.group(1).strip()
        message_content = message_match.group(2).strip()

        execute_create_channel_and_send_message(
            db=db,
            user=user,
            channel_name=channel_name,
            message_content=message_content,
        )

        task.status = "completed"
        db.commit()
        db.refresh(task)

        return task

    channel_match = re.fullmatch(
        r"Create a channel called (.+?)\.?",
        instruction,
        re.IGNORECASE,
    )

    if channel_match:
        channel_name = channel_match.group(1).strip()

        execute_create_channel(
            db=db,
            user=user,
            channel_name=channel_name,
        )

        db.commit()

        task.status = "completed"
        db.commit()
        db.refresh(task)

        return task

    task.status = "failed"
    db.commit()
    db.refresh(task)

    return task
