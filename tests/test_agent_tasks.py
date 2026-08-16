from uuid import uuid4

from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.user import User
from app.security import hash_password
from app.services.agent_executor import (
    execute_create_channel_and_send_message,
    execute_agent_task,
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


def test_create_agent_task_executes_channel(
    authenticated_client,
    db,
    test_user,
):
    channel_name = f"engineering-{uuid4().hex[:8]}"

    response = authenticated_client.post(
        "/agent-tasks/",
        json={
            "instruction": f"Create a channel called {channel_name}.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "completed"
    assert data["user_id"] == test_user.id

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None
    assert channel.created_by == test_user.id


def test_create_agent_task_executes_channel_and_message(
    authenticated_client,
    db,
    test_user,
):
    channel_name = f"devops-{uuid4().hex[:8]}"
    message_content = "Deployment completed."

    response = authenticated_client.post(
        "/agent-tasks/",
        json={
            "instruction": (
                f"Create a channel called {channel_name} "
                f"and send the message {message_content}"
            ),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "completed"
    assert data["user_id"] == test_user.id

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None

    message = db.query(Message).filter(
        Message.channel_id == channel.id,
        Message.user_id == test_user.id,
        Message.content == message_content,
    ).first()

    assert message is not None


def test_create_agent_task_unsupported_instruction_fails(
    authenticated_client,
    db,
    test_user,
):
    response = authenticated_client.post(
        "/agent-tasks/",
        json={
            "instruction": "Delete the entire database.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "failed"
    assert data["user_id"] == test_user.id

    task = db.query(AgentTask).filter(
        AgentTask.id == data["id"]
    ).first()

    assert task is not None
    assert task.status == "failed"


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


def test_execute_agent_task_marks_completed(db, test_user):
    channel_name = f"engineering-{uuid4().hex[:8]}"

    task = AgentTask(
        instruction=f"Create a channel called {channel_name}.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "completed"


def test_execute_agent_task_marks_unsupported_as_failed(db, test_user):
    task = AgentTask(
        instruction="Do something unsupported.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "failed"


def test_execute_agent_task_is_case_insensitive(db, test_user):
    channel_name = f"support-{uuid4().hex[:8]}"

    task = AgentTask(
        instruction=f"CREATE A CHANNEL CALLED {channel_name}.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "completed"

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None


def test_execute_agent_task_strips_instruction_whitespace(
    db,
    test_user,
):
    channel_name = f"qa-{uuid4().hex[:8]}"

    task = AgentTask(
        instruction=f"   Create a channel called {channel_name}.   ",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "completed"

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None


def test_execute_agent_task_channel_and_message_case_insensitive(
    db,
    test_user,
):
    channel_name = f"deployments-{uuid4().hex[:8]}"
    message_content = "Deployment completed."

    task = AgentTask(
        instruction=(
            f"CREATE A CHANNEL CALLED {channel_name} "
            f"AND SEND THE MESSAGE {message_content}"
        ),
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "completed"

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None

    message = db.query(Message).filter(
        Message.channel_id == channel.id,
        Message.user_id == test_user.id,
        Message.content == message_content,
    ).first()

    assert message is not None


def test_execute_agent_task_with_quoted_message(db, test_user):
    channel_name = f"deployments-{uuid4().hex[:8]}"
    message_content = "Deployment completed successfully."

    task = AgentTask(
        instruction=(
            f'Create a channel called {channel_name} '
            f'and send the message "{message_content}"'
        ),
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    assert result.status == "completed"

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None

    message = db.query(Message).filter(
        Message.channel_id == channel.id,
        Message.user_id == test_user.id,
        Message.content == message_content,
    ).first()

    assert message is not None


def test_execute_agent_task_endpoint(
    authenticated_client,
    db,
    test_user,
):
    channel_name = f"endpoint-{uuid4().hex[:8]}"

    task = AgentTask(
        instruction=f"Create a channel called {channel_name}.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = authenticated_client.post(
        f"/agent-tasks/{task.id}/execute"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["status"] == "completed"
    assert data["user_id"] == test_user.id

    channel = db.query(Channel).filter(
        Channel.name == channel_name
    ).first()

    assert channel is not None
    assert channel.created_by == test_user.id


def test_execute_agent_task_endpoint_unsupported_instruction(
    authenticated_client,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Do something unsupported.",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = authenticated_client.post(
        f"/agent-tasks/{task.id}/execute"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task.id
    assert data["status"] == "failed"


def test_execute_agent_task_endpoint_not_found(
    authenticated_client,
):
    response = authenticated_client.post(
        "/agent-tasks/999999/execute"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent task not found"


def test_execute_agent_task_endpoint_blocks_other_user(
    authenticated_client,
    db,
    test_user,
):
    other_user = User(
        username=f"otheruser_{uuid4().hex[:8]}",
        email=f"other-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("password123"),
    )

    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    task = AgentTask(
        instruction="Create a channel called other-user-channel.",
        status="pending",
        user_id=other_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = authenticated_client.get("/agent-tasks/")

    assert response.status_code == 200

    data = response.json()

    assert all(item["user_id"] == test_user.id for item in data)
    assert not any(item["id"] == task.id for item in data)

