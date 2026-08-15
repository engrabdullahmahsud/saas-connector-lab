import pytest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

from app.database import SessionLocal
from app.models.agent_task import AgentTask
from app.models.channel import Channel
from app.models.channel_member import ChannelMember
from app.models.message import Message
from app.models.user import User
from app.security import hash_password


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db):
    unique_id = uuid4().hex[:8]

    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Remove agent tasks belonging to this user.
    db.query(AgentTask).filter(
        AgentTask.user_id == user.id
    ).delete(synchronize_session=False)

    # Find channels created by this user.
    channel_ids = [
        channel.id
        for channel in db.query(Channel).filter(
            Channel.created_by == user.id
        ).all()
    ]

    if channel_ids:
        # Messages must be deleted before channels because of the FK.
        db.query(Message).filter(
            Message.channel_id.in_(channel_ids)
        ).delete(synchronize_session=False)

        db.query(ChannelMember).filter(
            ChannelMember.channel_id.in_(channel_ids)
        ).delete(synchronize_session=False)

        db.query(Channel).filter(
            Channel.id.in_(channel_ids)
        ).delete(synchronize_session=False)

    # Remove memberships the user has in other channels.
    db.query(ChannelMember).filter(
        ChannelMember.user_id == user.id
    ).delete(synchronize_session=False)

    # Remove messages authored by the user in channels they don't own.
    db.query(Message).filter(
        Message.user_id == user.id
    ).delete(synchronize_session=False)

    db.delete(user)
    db.commit()


@pytest.fixture
def test_channel(db, test_user):
    channel = Channel(
        name=f"test-channel-{uuid4().hex[:8]}",
        description="Test channel",
        created_by=test_user.id,
    )

    db.add(channel)
    db.commit()
    db.refresh(channel)

    yield channel

    db.query(Message).filter(
        Message.channel_id == channel.id
    ).delete(synchronize_session=False)

    db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel.id
    ).delete(synchronize_session=False)

    db.delete(channel)
    db.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client(client, test_user):
    from app.auth import create_access_token

    token = create_access_token(
        data={"sub": str(test_user.id)}
    )

    client.headers.update(
        {"Authorization": f"Bearer {token}"}
    )

    return client
