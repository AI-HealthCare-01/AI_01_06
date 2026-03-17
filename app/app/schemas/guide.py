from pydantic import BaseModel


class GuideCreateRequest(BaseModel):
    prescription_id: int
    force: bool = False


class GuideResponse(BaseModel):
    id: int
    prescription_id: int
    content: dict
    created_at: str
