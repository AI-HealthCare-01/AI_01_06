from pydantic import BaseModel


class GuideRequest(BaseModel):
    prescription_id: int
    ocr_result: str
    user_profile: dict


class GuideResponse(BaseModel):
    guide_text: str
    disclaimer: str
