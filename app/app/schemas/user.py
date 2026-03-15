from pydantic import BaseModel, Field


class PatientProfileData(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    has_allergy: bool = False
    allergy_details: str | None = None
    has_disease: bool = False
    disease_details: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    name: str
    role: str
    birth_date: str | None = None
    gender: str | None = None
    phone: str | None = None
    font_size_mode: str | None = None
    patient_profile: PatientProfileData | None = None


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=100)
    font_size_mode: str | None = None
    height_cm: float | None = Field(default=None, ge=50.0, le=300.0)
    weight_kg: float | None = Field(default=None, ge=10.0, le=500.0)
    has_allergy: bool | None = None
    allergy_details: str | None = Field(default=None, max_length=1000)
    has_disease: bool | None = None
    disease_details: str | None = Field(default=None, max_length=1000)
