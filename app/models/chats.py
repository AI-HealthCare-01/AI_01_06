"""
chats 도메인 Tortoise ORM 모델 (CharEnumField 적용).

기준: docs/dev/Sullivan_Init.sql
포함 테이블:
  - chat_sessions
  - chat_messages
  - chat_feedbacks
"""

import uuid

from tortoise import fields, models

from app.core.enums import SenderType
from app.models.guides import MedicationGuide
from app.models.medicals import Prescription
from app.models.users import User


class ChatSession(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    patient: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="chat_sessions"
    )
    prescription: fields.ForeignKeyRelation[Prescription] = fields.ForeignKeyField(
        "models.Prescription", related_name="chat_sessions", null=True
    )
    guide: fields.ForeignKeyRelation[MedicationGuide] = fields.ForeignKeyField(
        "models.MedicationGuide", related_name="chat_sessions", null=True
    )
    started_at = fields.DatetimeField(auto_now_add=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "chat_sessions"


class ChatMessage(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    session: fields.ForeignKeyRelation[ChatSession] = fields.ForeignKeyField(
        "models.ChatSession", related_name="messages"
    )
    sender_type = fields.CharEnumField(SenderType, max_length=20)
    message_text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"


class ChatFeedback(models.Model):
    id = fields.CharField(max_length=36, pk=True, default=lambda: str(uuid.uuid4()))
    message: fields.OneToOneRelation[ChatMessage] = fields.OneToOneField(
        "models.ChatMessage", related_name="feedback"
    )
    feedback_category = fields.CharField(max_length=255)
    additional_notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_feedbacks"
