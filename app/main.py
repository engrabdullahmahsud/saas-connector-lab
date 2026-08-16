from fastapi import FastAPI

from app.models import User, Channel, ChannelMember, Message

from app.api.users import router as users_router
from app.api.channels import router as channels_router
from app.api.channel_members import router as channel_members_router
from app.api.messages import router as messages_router
from app.api.auth import router as auth_router
from app.api.agent_tasks import router as agent_tasks_router
from app.services.redis_service import ping_redis


app = FastAPI(title="SaaS Connector Lab")


app.include_router(users_router)
app.include_router(channels_router)
app.include_router(channel_members_router)
app.include_router(messages_router)
app.include_router(auth_router)
app.include_router(agent_tasks_router)


@app.get("/")
def root():
    return {"message": "SaaS Connector Lab is running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "redis": "ok" if ping_redis() else "unavailable",
    }
