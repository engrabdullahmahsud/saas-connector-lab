from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.authorization import require_channel_member
from app.database import get_db
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse


router = APIRouter(
    prefix="/channels",
    tags=["messages"],
)


@router.post(
    "/{channel_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    channel_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(require_channel_member),
    db: Session = Depends(get_db),
):
    channel = db.query(Channel).filter(
        Channel.id == channel_id
    ).first()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    message = Message(
        content=message_data.content,
        user_id=current_user.id,
        channel_id=channel_id,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get(
    "/{channel_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    channel_id: int,
    current_user: User = Depends(require_channel_member),
    db: Session = Depends(get_db),
):
    channel = db.query(Channel).filter(
        Channel.id == channel_id
    ).first()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.channel_id == channel_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return messages


@router.delete(
    "/{channel_id}/messages/{message_id}",
    status_code=status.HTTP_200_OK,
)
def delete_message(
    channel_id: int,
    message_id: int,
    current_user: User = Depends(require_channel_member),
    db: Session = Depends(get_db),
):
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.channel_id == channel_id,
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages",
        )

    db.delete(message)
    db.commit()

    return {
        "detail": "Message deleted successfully"
    }
