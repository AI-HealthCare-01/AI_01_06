from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.dtos.auth import FontMode, UserRole
from app.dtos.base import BaseSerializerModel
from app.models.users import Gender
from app.validators.common import optional_after_validator
from app.validators.user_validators import validate_birthday, validate_phone_number


class UserUpdateRequest(BaseModel):
    name: Annotated[str | None, Field(None, min_length=2, max_length=100, description="이름")]
    phone: Annotated[
        str | None,
        Field(None, description="Available Format: +8201011112222, 01011112222, 010-1111-2222"),
        optional_after_validator(validate_phone_number),
    ]


class AccessibilityUpdateRequest(BaseModel):
    font_mode: Annotated[FontMode, Field(..., description="글자 크기 모드")]


class UserInfoResponse(BaseSerializerModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    user_id: Annotated[str, Field(alias="id")]
    email: str
    name: str
    birth_date: Annotated[date, Field(alias="birthdate")]
    gender: Gender
    role: UserRole
    font_mode: FontMode | None = None
