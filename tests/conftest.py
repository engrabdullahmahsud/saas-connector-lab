import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token
from app.database import Base, get_db
from app.main import app
from app.security import hash_password


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:",
)


# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

if TEST_DATABASE_URL == "sqlite:///:memory:":
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
        if TEST_DATABASE_URL.startswith("sqlite")
        else {},
    )


# SQLite does not enforce foreign-key constraints by default.
# Enable them for every SQLite connection so ON DELETE CASCADE works.
if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def set_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()

        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Database dependency override
# ---------------------------------------------------------------------------

def override_get_db():
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Database lifecycle
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=engine)

    # Install the override for the entire test session.
    # This also covers tests that create TestClient(app) directly.
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.pop(get_db, None)

    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Clean database before every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()

    try:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())

        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()

    yield


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Test client
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user(db):
    from app.models.user import User

    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def second_user(db):
    from app.models.user import User

    user = User(
        username="seconduser",
        email="seconduser@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(
        data={"sub": str(test_user.id)}
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def second_auth_headers(second_user):
    token = create_access_token(
        data={"sub": str(second_user.id)}
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def authenticated_client(client, auth_headers):
    client.headers.update(auth_headers)
    return client


# ---------------------------------------------------------------------------
# Channel
# ---------------------------------------------------------------------------

@pytest.fixture
def test_channel(db, test_user):
    from app.models.channel import Channel

    channel = Channel(
        name="test-channel",
        description="Test channel",
        created_by=test_user.id,
    )

    db.add(channel)
    db.commit()
    db.refresh(channel)

    return channel
