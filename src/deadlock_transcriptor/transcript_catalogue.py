"""
Readers for external Deadlock voice-line transcript catalogues
"""

import json
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path


class TranscriptPriority(IntEnum):
    """
    Authority order for transcript revisions
    """

    GENERATED = 1
    MANUAL = 2
    OFFICIAL = 3


class TranscriptSchemaVersion(IntEnum):
    """
    Supported schema version of the external transcript catalogue
    """

    THREE = 3


class TranscriptRevisionSource(StrEnum):
    """
    Source values supported by the external transcript schema
    """

    GENERATED = "generated"
    MANUAL = "manual"
    OFFICIAL = "official"

    @property
    def priority(
        self,
    ) -> TranscriptPriority:
        """
        Return the authority order of this revision source
        """
        return TranscriptPriority[self.name]


@dataclass(frozen=True, slots=True)
class CatalogueEntry:
    """
    Text and provenance loaded from a schema-v3 transcript revision
    """

    text: str
    meta: dict[str, str]


def load_hero_transcript_catalogue(
    *,
    roots: tuple[Path, ...],
    hero: str,
) -> dict[str, dict[str, CatalogueEntry]]:
    """
    Load one hero's transcript text by normalized path and audio SHA-256
    """
    transcripts: dict[str, dict[str, tuple[TranscriptPriority, CatalogueEntry]]] = {}
    for root in roots:
        hero_root = _find_hero_root(root=root, hero=hero)
        if hero_root is None:
            continue
        for path in hero_root.rglob("*.json"):
            _load_catalogue_file(path=path, transcripts=transcripts)
    return {
        filename: {digest: entry for digest, (_priority, entry) in entries.items()}
        for filename, entries in transcripts.items()
    }


def find_transcript(
    *,
    catalogue: dict[str, dict[str, CatalogueEntry]],
    audio_id: str,
    digest: str,
) -> CatalogueEntry | None:
    """
    Return a transcript when its normalized path and SHA-256 both match
    """
    return catalogue.get(_normalize_transcript_path(path=audio_id), {}).get(digest.casefold())


def _find_hero_root(
    *,
    root: Path,
    hero: str,
) -> Path | None:
    if not root.is_dir():
        return None
    for child in root.iterdir():
        if child.is_dir() and child.name.casefold() == hero.casefold():
            return child
    return None


def _load_catalogue_file(
    *,
    path: Path,
    transcripts: dict[str, dict[str, tuple[TranscriptPriority, CatalogueEntry]]],
) -> None:
    try:
        with path.open(encoding="utf-8") as file:
            payload: object = json.load(file)
    except (OSError, json.JSONDecodeError):
        return
    if (
        not isinstance(payload, dict)
        or payload.get("schemaVersion") != TranscriptSchemaVersion.THREE
    ):
        return
    filename = payload.get("filename")
    if not isinstance(filename, str):
        return
    revisions = payload.get("revisions")
    if not isinstance(revisions, list):
        return
    for revision in revisions:
        _add_revision(
            filename=filename,
            revision=revision,
            transcripts=transcripts,
        )


def _add_revision(
    *,
    filename: str,
    revision: object,
    transcripts: dict[str, dict[str, tuple[TranscriptPriority, CatalogueEntry]]],
) -> None:
    if not isinstance(revision, dict):
        return
    source_value = revision.get("source")
    text = revision.get("text")
    hashes = revision.get("sha256")
    if (
        not isinstance(source_value, str)
        or not isinstance(text, str)
        or not isinstance(hashes, list)
    ):
        return
    try:
        source = TranscriptRevisionSource(source_value)
    except ValueError:
        return
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return
    meta = {
        "schema_version": str(TranscriptSchemaVersion.THREE),
        "filename": filename,
        "source": source.value,
    }
    model = revision.get("model")
    if isinstance(model, str):
        meta["model"] = model
    entry = CatalogueEntry(text=cleaned_text, meta=meta)
    entries = transcripts.setdefault(_normalize_transcript_path(path=filename), {})
    for digest in hashes:
        if not isinstance(digest, str) or len(digest) != 64:
            continue
        normalized_digest = digest.casefold()
        existing = entries.get(normalized_digest)
        if existing is None or source.priority > existing[0]:
            entries[normalized_digest] = (source.priority, entry)


def _normalize_transcript_path(
    *,
    path: str,
) -> str:
    normalized = path.replace("\\", "/").strip("/").casefold()
    source_prefix = "sounds/vo/"
    if normalized.startswith(source_prefix):
        return normalized.removeprefix(source_prefix)
    return normalized
