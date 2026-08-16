SaaS Connector Lab

A FastAPI-based SaaS connector backend with authentication, users, channels, channel membership, messages, agent tasks, task execution, and automated task evaluation.

The project uses PostgreSQL for persistence, SQLAlchemy for ORM/database access, Alembic for migrations, and pytest for automated testing.

Features
User registration and authentication
JWT-based authentication
Password hashing with Argon2
User-owned resources
Channels
Channel membership
Messages
Agent tasks
Automatic agent task execution
Agent task evaluation
Task evaluation persistence
Ownership and authorization checks
PostgreSQL database
Alembic database migrations
Docker and Docker Compose support
GitHub Actions CI
Automated test suite
Tech Stack
Python 3.14
FastAPI
SQLAlchemy
PostgreSQL 16
Alembic
Pydantic
PyJWT
Argon2
pytest
Docker
GitHub Actions
Project Structure
saas-connector-lab/
├── app/
│   ├── api/
│   │   ├── agent_tasks.py
│   │   ├── auth.py
│   │   ├── channel_members.py
│   │   ├── channels.py
│   │   ├── messages.py
│   │   └── users.py
│   │
│   ├── models/
│   │   ├── agent_task.py
│   │   ├── channel.py
│   │   ├── channel_member.py
│   │   ├── message.py
│   │   ├── task_evaluation.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │   ├── agent_task.py
│   │   ├── auth.py
│   │   ├── channel.py
│   │   ├── channel_member.py
│   │   ├── message.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── agent_executor.py
│   │   └── task_evaluator.py
│   │
│   ├── auth.py
│   ├── authorization.py
│   ├── database.py
│   ├── main.py
│   └── security.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py
│   ├── test_agent_tasks.py
│   ├── test_channel_members.py
│   ├── test_channels.py
│   ├── test_messages.py
│   └── test_users.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
Architecture

The application follows a simple layered architecture:

Client
  │
  ▼
FastAPI API Routes
  │
  ├── Authentication
  ├── Authorization
  └── Request Validation
  │
  ▼
Services
  │
  ├── Agent Executor
  └── Task Evaluator
  │
  ▼
SQLAlchemy Models
  │
  ▼
PostgreSQL

API routes handle HTTP requests and authorization.

Services contain application logic such as executing agent instructions and evaluating whether the expected result was created.

SQLAlchemy models represent persistent database entities.

PostgreSQL stores all application data.

Database Models

The main entities are:

User

Represents an authenticated application user.

Channel

Represents a communication channel owned by a user.

ChannelMember

Associates users with channels.

Message

Represents a message sent by a user inside a channel.

AgentTask

Represents an instruction submitted to the agent.

An agent task contains:

Instruction
Status
User ownership
Creation timestamp
TaskEvaluation

Stores the result of evaluating an agent task.

An evaluation contains:

Task ID
Result
Evaluation checks
Creation timestamp

Task evaluations are associated with their parent agent task and are deleted when the parent task is deleted.

Environment Variables

Create a .env file containing:

DATABASE_URL=postgresql://postgres:postgres@localhost:5433/saas_connector
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

For production, use a strong randomly generated SECRET_KEY.

Do not commit .env or production secrets to source control.

Local Development
1. Create and activate the virtual environment
python3.14 -m venv .venv
source .venv/bin/activate
2. Install dependencies
pip install -r requirements.txt
3. Start PostgreSQL

Using Docker Compose:

docker compose up -d postgres

The PostgreSQL container is exposed locally on port 5433.

4. Run migrations
alembic upgrade head
5. Start the API
uvicorn app.main:app --reload

The API will be available at:

http://localhost:8000

FastAPI's interactive documentation is available at:

http://localhost:8000/docs
Docker

The complete application can be started with:

docker compose up --build

This starts:

PostgreSQL
FastAPI API

The API is exposed on port 8000.

PostgreSQL is exposed on port 5433.

Database Migrations

Alembic manages database schema changes.

Check the current migration:

alembic current

Show migration heads:

alembic heads

Apply all migrations:

alembic upgrade head

Create a new migration:

alembic revision --autogenerate -m "describe change"

The current migration chain includes:

83fea73de530  initial schema
713ae90bc26f  add agent tasks
017d0c9aa2f4  add user id to agent tasks
9955fae898df  add task evaluations
26fc5e80b214  cascade task evaluation deletes

The current migration head is:

26fc5e80b214
Authentication

Authentication uses JWT access tokens.

Users first authenticate through the authentication API and then provide the returned bearer token when accessing protected endpoints.

Example:

Authorization: Bearer <access_token>

Passwords are securely hashed using Argon2 rather than being stored as plaintext.

Agent Tasks

Agent tasks allow users to submit natural-language instructions.

For example:

Create a channel called Engineering

or:

Create a channel called Engineering and send the message "Deployment completed"

The agent executor interprets supported instructions and performs the requested database operations.

Task Lifecycle
pending
   │
   ▼
execution
   │
   ├── successful → completed
   │
   └── unsupported/failed → failed
Task Evaluation

Agent tasks can be evaluated after execution.

For a channel-and-message task, the evaluator checks:

Whether the expected channel exists
Whether the task owner is a member of the channel
Whether the expected message exists

The evaluation result is one of:

PASS
PARTIAL
FAIL
PASS

All required checks succeeded.

PARTIAL

At least one expected result exists, but not all checks succeeded.

FAIL

None of the required results were successfully created.

Evaluation records are persisted in the task_evaluations table.

API Endpoints
Authentication

Authentication endpoints are available under:

/auth
Users

User-related endpoints are available under:

/users
Channels

Channel endpoints are available under:

/channels
Channel Members

Membership endpoints are available under:

/channel-members
Messages

Message endpoints are available under:

/messages
Agent Tasks

Agent task endpoints are available under:

/agent-tasks

Important agent task operations include:

POST /agent-tasks/

Create and execute a new agent task.

GET /agent-tasks/

List the authenticated user's agent tasks.

POST /agent-tasks/{task_id}/execute

Execute an existing pending/failed task.

POST /agent-tasks/{task_id}/evaluate

Evaluate an agent task.

Example Agent Task

Request:

{
  "instruction": "Create a channel called Engineering and send the message \"Deployment completed\""
}

The executor creates the channel, ensures the user is a channel member, creates the message, and marks the task as completed.

The task can then be evaluated:

POST /agent-tasks/1/evaluate

Example evaluation:

{
  "task_id": 1,
  "result": "PASS",
  "checks": {
    "channel_created": true,
    "channel_member": true,
    "message_created": true
  }
}
Authorization

Protected resources are scoped to the authenticated user.

For example, agent tasks are queried using the authenticated user's ID:

AgentTask.user_id == current_user.id

This prevents one user from accessing another user's tasks.

Agent task evaluation also verifies ownership before allowing evaluation.

Testing

Run the complete test suite with:

pytest -v

The current test suite covers:

Users
Channels
Channel membership
Messages
Agent tasks
Task execution
Task evaluation
Authorization
Ownership restrictions
Error handling

Current test status:

67 passed
Continuous Integration

GitHub Actions runs automatically for pushes and pull requests targeting main.

The CI pipeline:

Starts PostgreSQL 16
Installs Python 3.14
Installs project dependencies
Runs Alembic migrations
Runs the complete pytest suite
Builds the Docker image

The Docker build runs after the test job succeeds.

Database Safety

Agent task evaluations use a foreign key relationship to their parent agent task.

The SQLAlchemy relationship is configured with:

cascade="all, delete-orphan"
passive_deletes=True

The database foreign key also uses cascading deletes.

This ensures that deleting an agent task does not leave orphaned task evaluation records.

Production Considerations

Before production deployment, the following should be addressed:

Use a production-grade secret key
Store secrets in a secure secret manager
Use HTTPS
Configure production CORS policies
Use a managed PostgreSQL database
Add structured application logging
Add request rate limiting
Add monitoring and health checks
Configure production database connection pooling
Review JWT expiration and refresh-token strategy
Restrict Docker and database network exposure
Run migrations as part of the deployment process
Development Workflow

Typical development workflow:

# Start database
docker compose up -d postgres

# Activate environment
source .venv/bin/activate

# Apply migrations
alembic upgrade head

# Run tests
pytest -v

# Start API
uvicorn app.main:app --reload

When changing database models:

alembic revision --autogenerate -m "describe change"
alembic upgrade head
pytest -v
Project Status

The core backend functionality is implemented and tested.

Current status:

Authentication: complete
Users: complete
Channels: complete
Channel membership: complete
Messages: complete
Agent tasks: complete
Agent execution: complete
Task evaluation: complete
Database migrations: complete
Authorization: complete
Automated tests: passing
Docker configuration: complete
CI pipeline: configured
Documentation: complete

The project is ready for final integration verification and deployment-oriented cleanup
