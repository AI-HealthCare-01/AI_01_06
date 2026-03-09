from tortoise import fields
from tortoise.models import Model


class TermsConsent(Model):
    user = fields.OneToOneField("models.User", related_name="terms_consent", primary_key=True)
    terms_of_service = fields.BooleanField()
    privacy_policy = fields.BooleanField()
    marketing_consent = fields.BooleanField(default=False)
    agreed_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "terms_consents"
