from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.task_evaluation import TaskEvaluation
from app.services.agent_executor import (
    execute_agent_task,
    execute_create_channel,
    execute_create_channel_and_send_message,
)
from app.services.task_evaluator import evaluate_agent_task


def test_list_agent_tasks(client, auth_headers):
    response = client.get(
        "/agent-tasks/",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_create_agent_task_executes_channel(client, auth_headers):
    response = client.post(
        "/agent-tasks/",
        json={
            "instruction": "Create a channel called Engineering",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["instruction"] == "Create a channel called Engineering"
    assert data["status"] == "completed"


def test_create_agent_task_executes_channel_and_message(
    client,
    auth_headers,
):
    response = client.post(
        "/agent-tasks/",
        json={
            "instruction": (
                'Create a channel called Engineering and '
                'send the message "Deployment completed"'
            ),
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "completed"


def test_create_agent_task_unsupported_instruction_fails(
    client,
    auth_headers,
):
    response = client.post(
        "/agent-tasks/",
        json={
            "instruction": "Delete the production database",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"


def test_execute_create_channel_and_send_message(
    db,
    test_user,
):
    channel = execute_create_channel_and_send_message(
        db=db,
        user=test_user,
        channel_name="Engineering",
        message_content="Deployment completed",
    )

    assert channel.name == "Engineering"

    membership = (
        db.query(ChannelMember)
        .filter(
            ChannelMember.channel_id == channel.id,
            ChannelMember.user_id == test_user.id,
        )
        .first()
    )

    assert membership is not None

    message = (
        db.query(Message)
        .filter(
            Message.channel_id == channel.id,
            Message.user_id == test_user.id,
            Message.content == "Deployment completed",
        )
        .first()
    )

    assert message is not None


def test_execute_reuses_existing_channel(
    db,
    test_user,
):
    first = execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    second = execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    assert first.id == second.id

    memberships = (
        db.query(ChannelMember)
        .filter(
            ChannelMember.channel_id == first.id,
            ChannelMember.user_id == test_user.id,
        )
        .all()
    )

    assert len(memberships) == 1


def test_execute_agent_task_marks_completed(
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
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


def test_execute_agent_task_marks_unsupported_as_failed(
    db,
    test_user,
):
    task = AgentTask(
        instruction="Do something unsupported",
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


def test_execute_agent_task_is_case_insensitive(
    db,
    test_user,
):
    task = AgentTask(
        instruction="CREATE A CHANNEL CALLED Engineering",
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


def test_execute_agent_task_strips_instruction_whitespace(
    db,
    test_user,
):
    task = AgentTask(
        instruction="   Create a channel called Engineering   ",
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


def test_execute_agent_task_channel_and_message_case_insensitive(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'CREATE A CHANNEL CALLED Engineering AND '
            'SEND THE MESSAGE "Deployment completed"'
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


def test_execute_agent_task_with_quoted_message(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed successfully"'
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

    message = (
        db.query(Message)
        .filter(
            Message.user_id == test_user.id,
            Message.content == "Deployment completed successfully",
        )
        .first()
    )

    assert message is not None


def test_execute_agent_task_is_idempotent_for_channel_and_message(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed"'
        ),
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    message_count_before = (
        db.query(Message)
        .filter(
            Message.user_id == test_user.id,
            Message.content == "Deployment completed",
        )
        .count()
    )

    execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    message_count_after = (
        db.query(Message)
        .filter(
            Message.user_id == test_user.id,
            Message.content == "Deployment completed",
        )
        .count()
    )

    assert message_count_before == 1
    assert message_count_after == 1



def test_execute_agent_task_endpoint(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.post(
        f"/agent-tasks/{task.id}/execute",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_execute_agent_task_endpoint_unsupported_instruction(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Unsupported command",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.post(
        f"/agent-tasks/{task.id}/execute",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_execute_agent_task_endpoint_not_found(
    client,
    auth_headers,
):
    response = client.post(
        "/agent-tasks/999999/execute",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_execute_agent_task_endpoint_blocks_other_user(
    client,
    auth_headers,
    second_auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.post(
        f"/agent-tasks/{task.id}/execute",
        headers=second_auth_headers,
    )

    assert response.status_code == 404


def test_execute_agent_task_endpoint_rejects_completed_task(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.post(
        f"/agent-tasks/{task.id}/execute",
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_evaluate_agent_task_passes_when_channel_and_message_exist(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed"'
        ),
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    assert result["result"] == "PASS"
    assert result["checks"]["channel_created"] is True
    assert result["checks"]["channel_member"] is True
    assert result["checks"]["message_created"] is True


def test_evaluate_agent_task_fails_when_nothing_was_created(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Missing and '
            'send the message "Nothing"'
        ),
        status="failed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    assert result["result"] == "FAIL"


def test_evaluate_agent_task_returns_partial_when_message_is_missing(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed"'
        ),
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    assert result["result"] == "PARTIAL"
    assert result["checks"]["channel_created"] is True
    assert result["checks"]["channel_member"] is True
    assert result["checks"]["message_created"] is False


def test_evaluate_agent_task_endpoint(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    response = client.post(
        f"/agent-tasks/{task.id}/evaluate",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_id"] == task.id
    assert data["result"] == "PASS"


def test_evaluate_agent_task_endpoint_blocks_other_user(
    client,
    second_auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.post(
        f"/agent-tasks/{task.id}/evaluate",
        headers=second_auth_headers,
    )

    assert response.status_code == 404


def test_evaluate_agent_task_does_not_accept_channel_owned_by_other_user(
    db,
    test_user,
    second_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    channel = execute_create_channel(
        db=db,
        user=second_user,
        channel_name="Engineering",
    )

    assert channel.created_by == second_user.id

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    assert result["result"] == "FAIL"


def test_evaluate_agent_task_requires_channel_membership(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed"'
        ),
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    channel = Channel(
        name="Engineering",
        description="Test channel",
        created_by=test_user.id,
    )

    db.add(channel)
    db.commit()
    db.refresh(channel)

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    assert result["result"] == "PARTIAL"
    assert result["checks"]["channel_created"] is True
    assert result["checks"]["channel_member"] is False
    assert result["checks"]["message_created"] is False


def test_evaluation_is_persisted(
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    result = evaluate_agent_task(
        db=db,
        task=task,
    )

    evaluation = (
        db.query(TaskEvaluation)
        .filter(TaskEvaluation.task_id == task.id)
        .first()
    )

    assert evaluation is not None
    assert evaluation.result == result["result"]


def test_evaluation_deleted_with_task(
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    evaluate_agent_task(
        db=db,
        task=task,
    )

    evaluation = (
        db.query(TaskEvaluation)
        .filter(TaskEvaluation.task_id == task.id)
        .first()
    )

    assert evaluation is not None

    db.delete(task)
    db.commit()

    remaining = (
        db.query(TaskEvaluation)
        .filter(TaskEvaluation.task_id == task.id)
        .first()
    )

    assert remaining is None


def test_list_task_evaluations_returns_history(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    first = evaluate_agent_task(db=db, task=task)
    second = evaluate_agent_task(db=db, task=task)

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] > data[1]["id"]
    assert data[0]["task_id"] == task.id
    assert data[0]["result"] == second["result"]
    assert data[1]["result"] == first["result"]


def test_list_task_evaluations_returns_empty_history(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_task_evaluations_not_found(
    client,
    auth_headers,
):
    response = client.get(
        "/agent-tasks/999999/evaluations",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_list_task_evaluations_blocks_other_user(
    client,
    second_auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations",
        headers=second_auth_headers,
    )

    assert response.status_code == 404


def test_list_task_evaluations_supports_limit_and_offset(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="completed",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_create_channel(
        db=db,
        user=test_user,
        channel_name="Engineering",
    )

    evaluate_agent_task(db=db, task=task)
    evaluate_agent_task(db=db, task=task)
    evaluate_agent_task(db=db, task=task)

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations?limit=2&offset=1",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] > data[1]["id"]


def test_list_task_evaluations_rejects_invalid_pagination(
    client,
    auth_headers,
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations?limit=0",
        headers=auth_headers,
    )

    assert response.status_code == 422

    response = client.get(
        f"/agent-tasks/{task.id}/evaluations?offset=-1",
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_execute_agent_task_does_not_rerun_completed_channel_task(
    db,
    test_user,
):
    task = AgentTask(
        instruction="Create a channel called Engineering",
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    first = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    channel_count_before = (
        db.query(Channel)
        .filter(Channel.name == "Engineering")
        .count()
    )

    second = execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    channel_count_after = (
        db.query(Channel)
        .filter(Channel.name == "Engineering")
        .count()
    )

    assert first.status == "completed"
    assert second.status == "completed"
    assert channel_count_before == 1
    assert channel_count_after == 1


def test_execute_agent_task_does_not_duplicate_completed_message_task(
    db,
    test_user,
):
    task = AgentTask(
        instruction=(
            'Create a channel called Engineering and '
            'send the message "Deployment completed"'
        ),
        status="pending",
        user_id=test_user.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    message_count_before = (
        db.query(Message)
        .filter(
            Message.user_id == test_user.id,
            Message.content == "Deployment completed",
        )
        .count()
    )

    execute_agent_task(
        db=db,
        task=task,
        user=test_user,
    )

    message_count_after = (
        db.query(Message)
        .filter(
            Message.user_id == test_user.id,
            Message.content == "Deployment completed",
        )
        .count()
    )

    assert message_count_before == 1
    assert message_count_after == 1
