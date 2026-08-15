from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.authorization import require_channel_owner
from app.database import get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.user import User
from app.schemas.channel_member import ChannelMemberResponse


router = APIRouter(
    prefix="/channel-members",
    tags=["Channel Membership"],
)


@router.post(
    "/{channel_id}",
    response_model=ChannelMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def join_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
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

    existing_membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == current_user.id,
        ChannelMember.channel_id == channel_id,
    ).first()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this channel",
        )

    new_membership = ChannelMember(
        user_id=current_user.id,
        channel_id=channel_id,
    )

    db.add(new_membership)

    try:
        db.commit()
        db.refresh(new_membership)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this channel",
        )

    return new_membership


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_200_OK,
)
def leave_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
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

    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == current_user.id,
        ChannelMember.channel_id == channel_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this channel",
        )

    db.delete(membership)
    db.commit()

    return {
        "detail": "Left channel successfully"
    }


@router.delete(
    "/{channel_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
)
def remove_channel_member(
    channel_id: int,
    user_id: int,
    current_user: User = Depends(require_channel_owner),
    db: Session = Depends(get_db),
):
    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == user_id,
        ChannelMember.channel_id == channel_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this channel",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel owner cannot remove themselves",
        )

    db.delete(membership)
    db.commit()

    return {
        "detail": "Member removed successfully"
    }


@router.get(
    "/channel/{channel_id}",
    response_model=list[ChannelMemberResponse],
)
def get_channel_members(
    channel_id: int,
    current_user: User = Depends(get_current_user),
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

    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == current_user.id,
        ChannelMember.channel_id == channel_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this channel",
        )

    return db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id
    ).all()
