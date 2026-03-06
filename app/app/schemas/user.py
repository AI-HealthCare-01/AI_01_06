from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    name: str
    role: str
    birth_date: str | None = None
    gender: str | None = None
    phone: str | None = None
    height: float | None = None
    weight: float | None = None
    allergies: str | None = None
    conditions: str | None = None


class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    name: str | None = None
    height: float | None = None
    weight: float | None = None
    allergies: str | None = None
    conditions: str | None = None
