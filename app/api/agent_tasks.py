import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.agent_task import AgentTask
from app.models.user import User
from app.schemas.agent_task import (
    AgentTaskCreate,
    AgentTaskEvaluationResponse,
    AgentTaskEvaluationHistoryResponse,
    AgentTaskResponse,
)
from app.services.agent_executor import execute_agent_task
from app.services.task_evaluator import evaluate_agent_task


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_task = AgentTask(
        instruction=task.instruction,
        status="pending",
        user_id=current_user.id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return execute_agent_task(
        db=db,
        task=db_task,
        user=current_user,
    )


@router.post(
    "/{task_id}/execute",
    response_model=AgentTaskResponse,
)
def execute_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(AgentTask)
        .filter(
            AgentTask.id == task_id,
            AgentTask.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent task not found",
        )

    if task.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent task is already completed",
        )

    return execute_agent_task(
        db=db,
        task=task,
        user=current_user,
    )


@router.post(
    "/{task_id}/evaluate",
    response_model=AgentTaskEvaluationResponse,
)
def evaluate_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(AgentTask)
        .filter(
            AgentTask.id == task_id,
            AgentTask.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent task not found",
        )

    return evaluate_agent_task(
        db=db,
        task=task,
    )


@router.get(
    "/{task_id}/evaluations",
    response_model=list[AgentTaskEvaluationHistoryResponse],
)
def list_task_evaluations(
    task_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.task_evaluation import TaskEvaluation

    task = (
        db.query(AgentTask)
        .filter(
            AgentTask.id == task_id,
            AgentTask.user_id == current_user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent task not found",
        )

    evaluations = (
        db.query(TaskEvaluation)
        .filter(TaskEvaluation.task_id == task.id)
        .order_by(TaskEvaluation.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": evaluation.id,
            "task_id": evaluation.task_id,
            "result": evaluation.result,
            "checks": json.loads(evaluation.checks),
            "created_at": evaluation.created_at,
        }
        for evaluation in evaluations
    ]


@router.get(
    "/",
    response_model=list[AgentTaskResponse],
)
def list_agent_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(AgentTask)
        .filter(AgentTask.user_id == current_user.id)
        .order_by(AgentTask.id.desc())
        .all()
    )
