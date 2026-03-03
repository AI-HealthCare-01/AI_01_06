from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DataT = TypeVar("DataT")


class BaseSerializerModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GenericResponse(BaseModel, Generic[DataT]):
    success: bool
    data: DataT | None = None
    error: dict | None = None
