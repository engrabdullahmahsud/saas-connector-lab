from pydantic import BaseModel, ConfigDict


class ChannelMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    channel_id: int
