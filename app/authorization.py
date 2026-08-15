from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.user import User


def get_channel_or_404(
    channel_id: int,
    db: Session,
):
    channel = db.query(Channel).filter(
        Channel.id == channel_id
    ).first()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    return channel


def require_channel_member(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = db.query(ChannelMember).filter(
        ChannelMember.user_id == current_user.id,
        ChannelMember.channel_id == channel_id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this channel",
        )

    return current_user


def require_channel_owner(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    channel = get_channel_or_404(
        channel_id,
        db,
    )

    if channel.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the channel owner can delete this channel",
        )

    return current_user
