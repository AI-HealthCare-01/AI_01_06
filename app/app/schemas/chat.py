from typing import Literal

from pydantic import BaseModel, Field


class ThreadCreateRequest(BaseModel):
    prescription_id: int | None = None


class MessageSendRequest(BaseModel):
    thread_id: int
    content: str = Field(min_length=1)


class FeedbackRequest(BaseModel):
    thread_id: int | None = None
    message_id: int | None = None
    feedback_type: Literal["thumbs_up", "thumbs_down", "session_positive", "session_negative"]
    reason: str | None = None
    reason_text: str | None = None
