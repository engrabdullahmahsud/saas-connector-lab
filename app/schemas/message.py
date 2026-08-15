from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    content: str
    user_id: int
    channel_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
