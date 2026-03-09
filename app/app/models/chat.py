from tortoise import fields
from tortoise.models import Model


class ChatThread(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="chat_threads")
    prescription = fields.ForeignKeyField(
        "models.Prescription", null=True, related_name="chat_threads"
    )
    title = fields.CharField(max_length=40, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "chat_threads"


class ChatMessage(Model):
    id = fields.IntField(primary_key=True)
    thread = fields.ForeignKeyField("models.ChatThread", related_name="messages")
    role = fields.CharField(max_length=20)
    content = fields.TextField()
    status = fields.CharField(max_length=20, default="completed")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"


class ChatFeedback(Model):
    id = fields.IntField(primary_key=True)
    thread = fields.ForeignKeyField("models.ChatThread", null=True, related_name="feedbacks")
    message = fields.ForeignKeyField("models.ChatMessage", null=True, related_name="feedbacks")
    feedback_type = fields.CharField(max_length=20)
    reason = fields.CharField(max_length=50, null=True)
    reason_text = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_feedbacks"
