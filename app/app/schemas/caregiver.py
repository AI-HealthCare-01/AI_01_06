from pydantic import BaseModel, field_validator


class MappingStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("APPROVED", "REJECTED"):
            raise ValueError("status는 APPROVED 또는 REJECTED여야 합니다.")
        return v
