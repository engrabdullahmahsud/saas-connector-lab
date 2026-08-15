from app.models.agent_task import AgentTask


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
