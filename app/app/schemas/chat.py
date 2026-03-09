from pydantic import BaseModel


class ThreadCreateRequest(BaseModel):
    prescription_id: int | None = None


class MessageSendRequest(BaseModel):
    thread_id: int
    content: str


class FeedbackRequest(BaseModel):
    thread_id: int | None = None
    message_id: int | None = None
    feedback_type: str
    reason: str | None = None
    reason_text: str | None = None
