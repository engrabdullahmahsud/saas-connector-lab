from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_task import AgentTask
from app.schemas.agent_task import AgentTaskCreate, AgentTaskResponse


router = APIRouter(
    prefix="/agent-tasks",
    tags=["Agent Tasks"],
)


@router.post(
    "/",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_task(
    task: AgentTaskCreate,
    db: Session = Depends(get_db),
):
    db_task = AgentTask(
        instruction=task.instruction,
        status="pending",
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get(
    "/",
    response_model=list[AgentTaskResponse],
)
def list_agent_tasks(
    db: Session = Depends(get_db),
):
    return db.query(AgentTask).order_by(AgentTask.id.desc()).all()
