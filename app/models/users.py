from tortoise import fields, models


class User(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255, null=True)
    name = fields.CharField(max_length=100)
    nickname = fields.CharField(max_length=50, unique=True)
    phone_number = fields.CharField(max_length=20, null=True)
    gender = fields.CharField(max_length=20)
    birthdate = fields.DateField()
    role = fields.CharField(max_length=20)
    font_size_mode = fields.CharField(max_length=20, null=True)
    failed_login_attempts = fields.IntField(default=0, null=True)
    locked_until = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)
    deleted_at = fields.DatetimeField(null=True, default=None)

    class Meta:
        table = "users"


class AuthProvider(models.Model):
    id = fields.CharField(max_length=36, pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="auth_providers"
    )
    provider = fields.CharField(max_length=30)
    provider_user_id = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)

    class Meta:
        table = "auth_providers"


class PatientProfile(models.Model):
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User", pk=True, related_name="patient_profile"
    )
    height_cm = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    weight_kg = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    has_allergies = fields.BooleanField(default=False, null=True)
    allergy_details = fields.TextField(null=True)
    has_diseases = fields.BooleanField(default=False, null=True)
    disease_details = fields.TextField(null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    class Meta:
        table = "patient_profiles"


class CaregiverPatientMapping(models.Model):
    caregiver: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="caring_for", to_field="id"
    )
    patient: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="caregivers", to_field="id"
    )
    status = fields.CharField(max_length=20)
    requested_at = fields.DatetimeField(auto_now_add=True, null=True)
    accepted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "caregiver_patient_mappings"
        unique_together = (("caregiver", "patient"),)


class TermsConsent(models.Model):
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User", pk=True, related_name="terms_consent"
    )
    terms_of_service = fields.BooleanField()
    privacy_policy = fields.BooleanField()
    marketing_consent = fields.BooleanField(default=False, null=True)
    agreed_at = fields.DatetimeField(auto_now_add=True, null=True)

    class Meta:
        table = "terms_consents"
