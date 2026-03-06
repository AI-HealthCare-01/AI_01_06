from pydantic import BaseModel


class GuideCreateRequest(BaseModel):
    prescription_id: int


class GuideResponse(BaseModel):
    id: int
    prescription_id: int
    content: dict
    created_at: str
