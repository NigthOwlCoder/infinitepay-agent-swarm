from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Validated public contract accepted by POST /chat."""

    message: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(min_length=1, max_length=128)
