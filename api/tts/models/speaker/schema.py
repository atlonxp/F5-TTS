from typing import Optional

from pydantic import BaseModel


class SpeakerIn(BaseModel):
    name: str
    reference_text: Optional[str] = None


class SpeakerOut(BaseModel):
    id: int
    name: str
    gender: str
    reference_text: Optional[str] = None
    reference_audio: Optional[str] = None
    duration: Optional[float] = None
