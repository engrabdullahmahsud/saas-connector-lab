from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentTaskCreate(BaseModel):
    instruction: str


class AgentTaskResponse(BaseModel):
    id: int
    instruction: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
