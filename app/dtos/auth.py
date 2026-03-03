from datetime import date
from enum import Enum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.models.users import Gender
from app.validators.user_validators import validate_birthday, validate_password, validate_phone_number


class UserRole(str, Enum):
    PATIENT = "PATIENT"
    CAREGIVER = "CAREGIVER"


class FontMode(str, Enum):
    NORMAL = "NORMAL"
    LARGE = "LARGE"


class SignUpRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: Annotated[
        EmailStr,
        Field(..., max_length=255, description="이메일(고유)"),
    ]
    password: Annotated[
        str,
        Field(..., min_length=8, description="비밀번호(8자+)"),
        AfterValidator(validate_password),
    ]
    name: Annotated[str, Field(..., max_length=100, description="이름")]
    birth_date: Annotated[
        date,
        Field(..., alias="birthdate", description="생년월일 YYYY-MM-DD"),
        AfterValidator(validate_birthday),
    ]
    gender: Annotated[Gender, Field(..., description="성별 (M/F)")]
    role: Annotated[UserRole, Field(..., description="역할 (PATIENT/CAREGIVER)")]


class LoginRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(..., min_length=8)]


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    role: UserRole


class TokenRefreshResponse(BaseModel):
    access_token: str
