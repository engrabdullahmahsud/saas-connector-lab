from uuid import uuid4

from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.services.agent_executor import (
    execute_create_channel_and_send_message,
)


def test_list_agent_tasks(authenticated_client, db, test_user):
    task = AgentTask(
        instruction="Create a channel called engineering.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = authenticated_client.get("/agent-tasks/")

    assert response.status_code == 200

    data = response.json()

    assert any(item["id"] == task.id for item in data)


def test_execute_create_channel_and_send_message(db, test_user):
    channel_name = f"engineering-{uuid4().hex[:8]}"

    channel = execute_create_channel_and_send_message(
        db=db,
        user=test_user,
        channel_name=channel_name,
        message_content="Deployment completed.",
    )

    assert channel.id is not None
    assert channel.name == channel_name
    assert channel.created_by == test_user.id

    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == test_user.id,
        ChannelMember.channel_id == channel.id,
    ).first()

    assert membership is not None

    message = db.query(Message).filter(
        Message.channel_id == channel.id,
        Message.user_id == test_user.id,
        Message.content == "Deployment completed.",
    ).first()

    assert message is not None


def test_execute_reuses_existing_channel(db, test_user):
    channel_name = f"engineering-{uuid4().hex[:8]}"

    existing_channel = Channel(
        name=channel_name,
        description="Existing channel",
        created_by=test_user.id,
    )

    db.add(existing_channel)
    db.commit()
    db.refresh(existing_channel)

    channel = execute_create_channel_and_send_message(
        db=db,
        user=test_user,
        channel_name=channel_name,
        message_content="Hello engineering.",
    )

    assert channel.id == existing_channel.id
    assert channel.name == channel_name

    channels = db.query(Channel).filter(
        Channel.name == channel_name
    ).all()

    assert len(channels) == 1

    message = db.query(Message).filter(
        Message.channel_id == existing_channel.id,
        Message.content == "Hello engineering.",
    ).first()

    assert message is not None
