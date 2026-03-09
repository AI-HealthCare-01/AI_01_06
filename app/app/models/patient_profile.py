from tortoise import fields
from tortoise.models import Model


class PatientProfile(Model):
    user = fields.OneToOneField("models.User", related_name="patient_profile", primary_key=True)
    height_cm = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    weight_kg = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    allergy_details = fields.TextField(null=True)
    disease_details = fields.TextField(null=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "patient_profiles"
