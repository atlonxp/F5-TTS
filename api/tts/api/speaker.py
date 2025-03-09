from typing import List

from ninja import File, UploadedFile
from ninja import Router

from ..models.speaker.models import Speaker
from ..models.speaker.schema import SpeakerOut, SpeakerIn

router = Router()


@router.get("/", response=List[SpeakerOut])
def list_speakers(request):
    """
    List all speakers available for voice cloning.
    """
    speakers = Speaker.objects.all()
    return speakers


@router.post("/", response=SpeakerOut)
def create_speaker(request, data: SpeakerIn, reference_audio: UploadedFile = File(...)):
    """
    Create a new speaker for voice cloning.
    - Expects JSON data with a speaker name and optional reference text.
    - Requires an uploaded reference_audio file.
    """
    # You might want to handle file storage with Django's default storage.
    speaker = Speaker.objects.create(
        name=data.name,
        reference_text=data.reference_text or "",
        reference_audio=reference_audio  # django-ninja handles UploadedFile for you.
    )
    return speaker
