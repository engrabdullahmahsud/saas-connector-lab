from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.authorization import require_channel_owner
from app.database import get_db
from app.models.channel import Channel
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelResponse


router = APIRouter(
    prefix="/channels",
    tags=["Channels"],
)


@router.post(
    "/",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_channel(
    channel: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_channel = db.query(Channel).filter(
        Channel.name == channel.name
    ).first()

    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Channel already exists",
        )

    new_channel = Channel(
        name=channel.name,
        description=channel.description,
        created_by=current_user.id,
    )

    db.add(new_channel)

    try:
        db.commit()
        db.refresh(new_channel)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Channel already exists",
        )

    return new_channel


@router.get(
    "/",
    response_model=list[ChannelResponse],
)
def get_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Channel).all()


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_200_OK,
)
def delete_channel(
    channel_id: int,
    current_user: User = Depends(require_channel_owner),
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

    db.delete(channel)
    db.commit()

    return {
        "detail": "Channel deleted successfully"
    }
