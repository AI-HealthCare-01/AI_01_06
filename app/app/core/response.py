from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: dict | list | None = None
    error: str | None = None


def success_response(data: dict | list | None = None) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(error: str) -> dict:
    return {"success": False, "data": None, "error": error}
