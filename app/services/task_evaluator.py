import json
import re

from sqlalchemy.orm import Session

from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.task_evaluation import TaskEvaluation


def _save_evaluation(
    db: Session,
    task: AgentTask,
    result: str,
    checks: dict,
) -> dict:
    evaluation = TaskEvaluation(
        task_id=task.id,
        result=result,
        checks=json.dumps(checks),
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return {
        "task_id": task.id,
        "result": result,
        "checks": checks,
    }


def evaluate_agent_task(
    db: Session,
    task: AgentTask,
) -> dict:
    instruction = task.instruction.strip()

    message_match = re.fullmatch(
        r'Create a channel called (.+?) and send the message ["\'](.+?)["\']',
        instruction,
        re.IGNORECASE,
    )

    if not message_match:
        message_match = re.fullmatch(
            r"Create a channel called (.+?) and send the message (.+)",
            instruction,
            re.IGNORECASE,
        )

    if message_match:
        channel_name = message_match.group(1).strip()
        message_content = message_match.group(2).strip()

        channel = (
            db.query(Channel)
            .filter(
                Channel.name == channel_name,
                Channel.created_by == task.user_id,
            )
            .first()
        )

        channel_created = channel is not None
        channel_member = False
        message_created = False

        if channel:
            membership = (
                db.query(ChannelMember)
                .filter(
                    ChannelMember.channel_id == channel.id,
                    ChannelMember.user_id == task.user_id,
                )
                .first()
            )

            channel_member = membership is not None

            if channel_member:
                message = (
                    db.query(Message)
                    .filter(
                        Message.channel_id == channel.id,
                        Message.user_id == task.user_id,
                        Message.content == message_content,
                    )
                    .first()
                )

                message_created = message is not None

        checks = {
            "channel_created": channel_created,
            "channel_member": channel_member,
            "message_created": message_created,
        }

        if all(checks.values()):
            result = "PASS"
        elif any(checks.values()):
            result = "PARTIAL"
        else:
            result = "FAIL"

        return _save_evaluation(
            db=db,
            task=task,
            result=result,
            checks=checks,
        )

    channel_match = re.fullmatch(
        r"Create a channel called (.+?)\.?",
        instruction,
        re.IGNORECASE,
    )

    if channel_match:
        channel_name = channel_match.group(1).strip()

        channel = (
            db.query(Channel)
            .filter(
                Channel.name == channel_name,
                Channel.created_by == task.user_id,
            )
            .first()
        )

        channel_created = channel is not None
        channel_member = False

        if channel:
            membership = (
                db.query(ChannelMember)
                .filter(
                    ChannelMember.channel_id == channel.id,
                    ChannelMember.user_id == task.user_id,
                )
                .first()
            )

            channel_member = membership is not None

        checks = {
            "channel_created": channel_created,
            "channel_member": channel_member,
        }

        if all(checks.values()):
            result = "PASS"
        elif any(checks.values()):
            result = "PARTIAL"
        else:
            result = "FAIL"

        return _save_evaluation(
            db=db,
            task=task,
            result=result,
            checks=checks,
        )

    return _save_evaluation(
        db=db,
        task=task,
        result="FAIL",
        checks={},
    )
