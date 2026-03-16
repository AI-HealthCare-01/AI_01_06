from pydantic import BaseModel


class MedicationSchema(BaseModel):
    id: int | None = None
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    instructions: str | None = None


class OcrResultResponse(BaseModel):
    hospital_name: str | None = None
    doctor_name: str | None = None
    prescription_date: str | None = None
    diagnosis: list[str] = []
    medications: list[MedicationSchema] = []


class OcrUpdateRequest(BaseModel):
    hospital_name: str | None = None
    doctor_name: str | None = None
    prescription_date: str | None = None
    diagnosis: list[str] = []
    medications: list[MedicationSchema] = []


class PrescriptionResponse(BaseModel):
    id: int
    image_path: str
    hospital_name: str | None = None
    doctor_name: str | None = None
    prescription_date: str | None = None
    diagnosis: list[str] = []
    ocr_status: str
    created_at: str
