from typing import Optional

from pydantic import BaseModel


class GenerateTTSInput(BaseModel):
    prompt_text: str
    reference_text: Optional[str] = ""


class GenerateTTSOutput(BaseModel):
    message: str
    generated_audio_path: str
    usage_log_id: int
