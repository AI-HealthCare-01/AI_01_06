"""
users 도메인 Tortoise ORM 모델.

기준: docs/dev/Sullivan_Init.sql
포함 테이블:
  - users
  - auth_providers
  - terms_consents
  - accessibility_settings
  - patient_profiles
  - caregiver_patient_mappings
"""

from tortoise import fields, models

from app.core.enums import AuthProvider, CaregiverMappingStatus, FontSizeMode, Gender, UserRole


class User(models.Model):
    """users 테이블"""

    id = fields.CharField(max_length=36, pk=True)  # VARCHAR(36) DEFAULT (UUID())
    email = fields.CharField(max_length=255, unique=True)  # UNIQUE NOT NULL
    password_hash = fields.CharField(max_length=255, null=True)  # 소셜 로그인 시 NULL 허용
    name = fields.CharField(max_length=100)
    nickname = fields.CharField(max_length=50, unique=True)  # 보호자-환자 검색/표시용 별명
    phone_number = fields.CharField(max_length=20, null=True)
    gender = fields.CharEnumField(Gender, max_length=1)
    birthdate = fields.DateField()  # 가이드/LLM 맥락 제공(연령)
    role = fields.CharEnumField(UserRole, max_length=20)  # PATIENT | GUARDIAN
    font_size_mode = fields.CharEnumField(FontSizeMode, max_length=20, null=True)
    failed_login_attempts = fields.IntField(default=0)  # 로그인 실패 횟수
    locked_until = fields.DatetimeField(null=True)  # 잠금 해제 시각
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True, default=None)  # 논리 삭제 시각

    class Meta:
        table = "users"


class AuthProviderModel(models.Model):
    """auth_providers 테이블"""

    id = fields.CharField(max_length=36, pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="auth_providers")
    provider = fields.CharEnumField(AuthProvider, max_length=30)  # LOCAL | KAKAO | NAVER | GOOGLE
    provider_user_id = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "auth_providers"
        unique_together = (("provider", "provider_user_id"),)


class TermsConsent(models.Model):
    """terms_consents 테이블"""

    user: fields.OneToOneRelation[User] = fields.OneToOneField("models.User", pk=True, related_name="terms_consent")
    terms_of_service = fields.BooleanField()  # 필수
    privacy_policy = fields.BooleanField()  # 필수
    marketing_consent = fields.BooleanField(default=False)  # 선택
    agreed_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "terms_consents"


class AccessibilitySetting(models.Model):
    """accessibility_settings 테이블"""

    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User", pk=True, related_name="accessibility_setting"
    )
    font_mode = fields.CharEnumField(FontSizeMode, max_length=20, null=True)  # SMALL | LARGE
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "accessibility_settings"


class PatientProfile(models.Model):
    """patient_profiles 테이블"""

    user: fields.OneToOneRelation[User] = fields.OneToOneField("models.User", pk=True, related_name="patient_profile")
    height_cm = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    weight_kg = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    has_allergies = fields.BooleanField(default=False)
    allergy_details = fields.TextField(null=True)  # 알러지/금기 정보
    has_diseases = fields.BooleanField(default=False)
    disease_details = fields.TextField(null=True)  # 기저질환/만성질환
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "patient_profiles"


class CaregiverPatientMapping(models.Model):
    """caregiver_patient_mappings 테이블"""

    caregiver: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="caring_for")
    patient: fields.ForeignKeyRelation[User] = fields.ForeignKeyField("models.User", related_name="caregivers")
    status = fields.CharEnumField(CaregiverMappingStatus, max_length=20)  # PENDING | APPROVED | REJECTED | REVOKED
    requested_at = fields.DatetimeField(auto_now_add=True)
    accepted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "caregiver_patient_mappings"
        unique_together = (("caregiver", "patient"),)
