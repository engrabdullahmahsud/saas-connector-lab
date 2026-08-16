import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.user import User


@dataclass
class ParsedAgentAction:
    action: str
    channel_name: str
    message_content: str | None = None


def parse_agent_instruction(
    instruction: str,
) -> ParsedAgentAction | None:
    instruction = instruction.strip()

    message_patterns = [
        r'Create a channel called (.+?) and send the message ["\'](.+?)["\']',
        r"Create a channel called (.+?) and send the message (.+)",
    ]

    for pattern in message_patterns:
        match = re.fullmatch(
            pattern,
            instruction,
            re.IGNORECASE,
        )

        if match:
            return ParsedAgentAction(
                action="create_channel_and_send_message",
                channel_name=match.group(1).strip(),
                message_content=match.group(2).strip(),
            )

    channel_match = re.fullmatch(
        r"Create a channel called (.+?)\.?",
        instruction,
        re.IGNORECASE,
    )

    if channel_match:
        return ParsedAgentAction(
            action="create_channel",
            channel_name=channel_match.group(1).strip(),
        )

    return None


def execute_create_channel(
    db: Session,
    user: User,
    channel_name: str,
) -> Channel:
    existing_channel = (
        db.query(Channel)
        .filter(
            Channel.name == channel_name,
            Channel.created_by == user.id,
        )
        .first()
    )

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

    membership = (
        db.query(ChannelMember)
        .filter(
            ChannelMember.user_id == user.id,
            ChannelMember.channel_id == channel.id,
        )
        .first()
    )

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

    existing_message = (
        db.query(Message)
        .filter(
            Message.channel_id == channel.id,
            Message.user_id == user.id,
            Message.content == message_content,
        )
        .first()
    )

    if existing_message is None:
        db.add(
            Message(
                content=message_content,
                user_id=user.id,
                channel_id=channel.id,
            )
        )

    db.commit()
    db.refresh(channel)

    return channel


def execute_agent_task(
    db: Session,
    task: AgentTask,
    user: User,
) -> AgentTask:
    parsed_action = parse_agent_instruction(
        task.instruction
    )

    if parsed_action is None:
        task.status = "failed"
        db.commit()
        db.refresh(task)

        return task

    if parsed_action.action == "create_channel":
        execute_create_channel(
            db=db,
            user=user,
            channel_name=parsed_action.channel_name,
        )

        task.status = "completed"
        db.commit()
        db.refresh(task)

        return task

    if parsed_action.action == "create_channel_and_send_message":
        execute_create_channel_and_send_message(
            db=db,
            user=user,
            channel_name=parsed_action.channel_name,
            message_content=parsed_action.message_content or "",
        )

        task.status = "completed"
        db.commit()
        db.refresh(task)

        return task

    task.status = "failed"
    db.commit()
    db.refresh(task)

    return task
