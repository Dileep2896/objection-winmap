import json
from pathlib import Path
from typing import Protocol

from .schemas import MeetingIn


class Transcriber(Protocol):
    def transcribe(self, source: Path) -> MeetingIn: ...


class FixtureTranscriber:
    """Local diarized fixtures stand in for Deepgram; no audio leaves this app."""

    def transcribe(self, source: Path) -> MeetingIn:
        data = json.loads(source.read_text())
        data.pop("id", None)
        return MeetingIn.model_validate(data)
