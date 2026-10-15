"""
Typed data models for the transcription catalogue
"""

from dataclasses import asdict, dataclass, field
from enum import StrEnum


class Source(StrEnum):
    """
    Origin of text in a transcription record
    """

    ORIGINAL = "original"
    MCALLBOSCO_DEADLOCK_TRANSCIPTIONS = "mcallbosco-deadlock-transciptions"
    QWEN_OLLAMA = "qwen-ollama"
    SUBTITLE = "subtitle"
    WHISPER = "whisper"


@dataclass(frozen=True, slots=True)
class LanguageText:
    """
    Text and provenance for one language
    """

    text: str
    source: Source
    meta: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Transcription:
    """
    One voice line in the portable output format
    """

    id: str
    hash: str
    text: dict[str, LanguageText]
    duration: float

    def as_dict(
        self,
    ) -> dict[str, object]:
        """
        Return a JSON-serializable representation of this voice line
        """
        return asdict(self)
