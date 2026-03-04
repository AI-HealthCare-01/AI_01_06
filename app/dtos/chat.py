from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.base import BaseSerializerModel


class ChatThreadCreateRequest(BaseModel):
    title: str | None = None


class ChatThreadResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: Annotated[str, Field(alias="id")]
    title: str | None = None


class ChatThreadListResponse(BaseModel):
    threads: list[ChatThreadResponse]
    page: int | None = None


class ChatMessageSendRequest(BaseModel):
    thread_id: str
    message: str
    context: dict | None = None


class ChatMessageSendResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: Annotated[str, Field(alias="id")]
    answer: str
    created_at: datetime


class ChatMessageSummary(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: Annotated[str, Field(alias="id")]
    message: Annotated[str, Field(alias="user_message")]
    answer: str
    created_at: datetime


class ChatMessageListResponse(BaseModel):
    messages: list[ChatMessageSummary]


class ChatFeedbackRating(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class ChatFeedbackRequest(BaseModel):
    message_id: str
    rating: ChatFeedbackRating
    comment: str | None = None


class ChatFeedbackResponse(BaseSerializerModel):
    model_config = ConfigDict(populate_by_name=True)

    feedback_id: Annotated[str, Field(alias="id")]
