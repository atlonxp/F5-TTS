from typing import Optional

from pydantic import BaseModel


class TTSConfigurationIn(BaseModel):
    current_model: str
    configuration: Optional[dict] = {}


class TTSConfigurationOut(BaseModel):
    id: int
    current_model: str
    configuration: Optional[dict] = {}
