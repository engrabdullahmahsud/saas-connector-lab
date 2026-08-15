from fastapi.testclient import TestClient

from app.main import app
from app.models.agent_task import AgentTask


client = TestClient(app)


def test_create_agent_task(db):
    response = client.post(
        "/agent-tasks/",
        json={
            "instruction": (
                "Create a channel called devops "
                "and send the message Deployment completed."
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["instruction"].startswith(
        "Create a channel called devops"
    )
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data

    task = db.query(AgentTask).filter(
        AgentTask.id == data["id"]
    ).first()

    assert task is not None
    assert task.status == "pending"


def test_list_agent_tasks(db):
    task = AgentTask(
        instruction="Create a channel called engineering.",
        status="pending",
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get("/agent-tasks/")

    assert response.status_code == 200

    data = response.json()

    assert any(item["id"] == task.id for item in data)
