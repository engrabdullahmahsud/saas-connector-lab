from pydantic import BaseModel, ConfigDict


class ChannelCreate(BaseModel):
    name: str
    description: str | None = None


class ChannelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_by: int
