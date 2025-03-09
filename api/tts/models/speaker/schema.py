from typing import Optional

from pydantic import BaseModel


class SpeakerIn(BaseModel):
    name: str
    reference_text: Optional[str] = None


class SpeakerOut(BaseModel):
    id: int
    name: str
    reference_text: Optional[str] = None
