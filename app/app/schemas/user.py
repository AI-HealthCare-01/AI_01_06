from pydantic import BaseModel


class PatientProfileData(BaseModel):
    height_cm: float | None = None
    weight_kg: float | None = None
    allergy_details: str | None = None
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
    nickname: str | None = None
    name: str | None = None
    font_size_mode: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    allergy_details: str | None = None
    disease_details: str | None = None
