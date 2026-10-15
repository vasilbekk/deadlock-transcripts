"""
Readers for subtitle files commonly found next to extracted game assets
"""

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path

SUBTITLE_SUFFIXES = frozenset({".json", ".srt", ".vtt"})
_TIMECODE_LINE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s+-->.*$")
_TAG = re.compile(r"<[^>]+>")


def load_subtitles(
    *,
    root: Path,
) -> dict[str, str]:
    """
    Load English subtitles, indexed by normalized audio path or stem
    """
    subtitles: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUBTITLE_SUFFIXES:
            continue
        for key, text in _read_subtitle_file(path=path, root=root).items():
            subtitles[_normalise_key(value=key)] = text
    return subtitles


def find_subtitle(
    *,
    subtitles: Mapping[str, str],
    audio_id: str,
) -> str | None:
    """
    Find a subtitle by full relative audio path, then by path stem
    """
    normalized_id = _normalise_key(value=audio_id)
    return subtitles.get(normalized_id) or subtitles.get(str(Path(normalized_id).with_suffix("")))


def _read_subtitle_file(
    *,
    path: Path,
    root: Path,
) -> dict[str, str]:
    if path.suffix.lower() == ".json":
        return _read_json(path=path)
    text = _read_timed_subtitle(path=path)
    if not text:
        return {}
    return {str(path.relative_to(root).with_suffix("")): text}


def _read_json(
    *,
    path: Path,
) -> dict[str, str]:
    with path.open(encoding="utf-8") as file:
        payload: object = json.load(file)
    return dict(_iter_json_entries(payload=payload))


def _iter_json_entries(
    *,
    payload: object,
) -> Iterable[tuple[str, str]]:
    if isinstance(payload, list):
        for item in payload:
            yield from _entry_to_pair(entry=item)
        return
    if not isinstance(payload, dict):
        return
    for container_key in ("entries", "subtitles", "lines"):
        entries = payload.get(container_key)
        if isinstance(entries, list):
            for item in entries:
                yield from _entry_to_pair(entry=item)
            return
    for key, value in payload.items():
        text = _english_text(value=value)
        if text is not None:
            yield key, text


def _entry_to_pair(
    *,
    entry: object,
) -> Iterable[tuple[str, str]]:
    if not isinstance(entry, dict):
        return
    identifier = next(
        (entry[key] for key in ("id", "path", "file", "audio") if isinstance(entry.get(key), str)),
        None,
    )
    text = _english_text(value=entry.get("text", entry.get("en")))
    if isinstance(identifier, str) and text is not None:
        yield identifier, text


def _english_text(
    *,
    value: object,
) -> str | None:
    if isinstance(value, str):
        return _clean_text(value=value)
    if isinstance(value, dict) and isinstance(value.get("en"), str):
        return _clean_text(value=value["en"])
    return None


def _read_timed_subtitle(
    *,
    path: Path,
) -> str:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    content = [line.strip() for line in lines if line.strip() and not line.isdigit()]
    content = [line for line in content if not _TIMECODE_LINE.match(line) and line != "WEBVTT"]
    return _clean_text(value=" ".join(content))


def _clean_text(
    *,
    value: str,
) -> str:
    return " ".join(_TAG.sub("", value).split())


def _normalise_key(
    *,
    value: str,
) -> str:
    return value.replace("\\", "/").lstrip("./").casefold()
