from typing import List

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from filer.models.filemodels import File as FilerFile
from ninja import File, UploadedFile, Form
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
@transaction.atomic
def create_speaker(request, data: Form[SpeakerIn], reference_audio: UploadedFile = File(...)):
    """
    Create a new speaker for voice cloning.
    - Expects JSON data with a speaker name and optional reference text.
    - Requires an uploaded reference_audio file.
    """

    relative_path = default_storage.save(f"speakers/{reference_audio.name}", ContentFile(reference_audio.read()))
    absolute_path = default_storage.path(relative_path)
    with open(absolute_path, "rb") as f:
        django_file = ContentFile(f.read(), name=relative_path)
        filer_file = FilerFile.objects.create(
            original_filename=reference_audio.name,
            file=django_file
        )

    speaker = Speaker.objects.create(
        name=data.name,
        gender=data.gender,
        reference_text=data.reference_text or "",
        reference_audio=filer_file,
        language=data.language,
    )
    return speaker
