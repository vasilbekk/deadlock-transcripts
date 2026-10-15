"""
Catalogue orchestration and audio metadata handling
"""

import hashlib
import json
import re
import subprocess
import wave
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from deadlock_transcriptor.models import LanguageText, Source, Transcription
from deadlock_transcriptor.progress import ProgressReporter
from deadlock_transcriptor.subtitles import find_subtitle, load_subtitles
from deadlock_transcriptor.transcript_catalogue import (
    find_transcript,
    load_hero_transcript_catalogue,
)

AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".opus"})


class Transcriber(Protocol):
    """
    Callable that produces English text for one audio file
    """

    def __call__(
        self,
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        """
        Transcribe the supplied audio file
        """


def build_catalogue(
    *,
    input_dir: Path,
    output_dir: Path,
    transcribe: Transcriber,
    whisper_model: str,
    hero_pattern: str | None = None,
    overwrite: bool = False,
    progress: ProgressReporter | None = None,
    transcript_dirs: tuple[Path, ...] = (),
    hero_prompts: dict[str, str] | None = None,
) -> int:
    """
    Build hero JSON files and return the number of processed audio files
    """
    input_dir = input_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _migrate_misgrouped_entries(
        output_dir=output_dir,
        hero_pattern=hero_pattern,
    )
    subtitles = load_subtitles(root=input_dir)
    audio_by_hero: defaultdict[str, list[Path]] = defaultdict(list)
    processed = 0
    for audio_path in _iter_audio_files(root=input_dir):
        audio_id = audio_path.relative_to(input_dir).as_posix()
        hero = _hero_name(audio_id=audio_id, pattern=hero_pattern)
        audio_by_hero[hero].append(audio_path)

    if progress is not None:
        progress.start(
            total=sum(len(audio_paths) for audio_paths in audio_by_hero.values()),
            hero_total=len(audio_by_hero),
        )

    heroes = sorted(audio_by_hero)
    for hero_index, hero in enumerate(heroes, start=1):
        if progress is not None:
            progress.start_hero(hero_name=hero, hero_index=hero_index)
        target = output_dir / f"{_safe_filename(value=hero)}.json"
        existing = _load_existing(path=target) if not overwrite else {}
        catalogue = load_hero_transcript_catalogue(
            roots=transcript_dirs,
            hero=hero,
        )
        initial_prompt = (hero_prompts or {}).get(hero.casefold())
        entries: list[Transcription] = []

        audio_paths = audio_by_hero.pop(hero)
        for audio_path in audio_paths:
            audio_id = audio_path.relative_to(input_dir).as_posix()
            digest = _sha256(path=audio_path)
            catalogue_entry = find_transcript(
                catalogue=catalogue,
                audio_id=audio_id,
                digest=digest,
            )
            if catalogue_entry is not None:
                entries.append(
                    Transcription(
                        id=audio_id,
                        hash=digest,
                        text={
                            "en": LanguageText(
                                text=catalogue_entry.text,
                                source=Source.MCALLBOSCO_DEADLOCK_TRANSCIPTIONS,
                                meta=catalogue_entry.meta,
                            )
                        },
                        duration=_duration_seconds(path=audio_path),
                    )
                )
                processed += 1
                if progress is not None:
                    progress.update(
                        source=Source.MCALLBOSCO_DEADLOCK_TRANSCIPTIONS,
                        reused=False,
                    )
                continue
            cached = existing.get(digest)
            if cached is not None:
                entries.append(
                    Transcription(
                        id=audio_id,
                        hash=digest,
                        text=cached.text,
                        duration=_duration_seconds(path=audio_path),
                    )
                )
                if progress is not None:
                    progress.update(source=cached.text["en"].source, reused=True)
                continue
            subtitle = find_subtitle(subtitles=subtitles, audio_id=audio_id)
            if subtitle is not None:
                text = subtitle
                source = Source.SUBTITLE
            else:
                if progress is not None:
                    progress.transcribing(audio_id=audio_id)
                text = transcribe(
                    audio_path=audio_path,
                    initial_prompt=initial_prompt,
                ).strip()
                if progress is not None:
                    progress.transcribed(audio_id=audio_id, text=text)
                source = Source.WHISPER
            entries.append(
                Transcription(
                    id=audio_id,
                    hash=digest,
                    text={
                        "en": LanguageText(
                            text=text.strip(),
                            source=source,
                            meta={"model": whisper_model} if source is Source.WHISPER else {},
                        )
                    },
                    duration=_duration_seconds(path=audio_path),
                )
            )
            processed += 1
            if progress is not None:
                progress.update(source=source, reused=False)
        _write_entries(path=target, entries=sorted(entries, key=lambda item: item.id))
        entries.clear()
        existing.clear()
        audio_paths.clear()
    if progress is not None:
        progress.finish()
    return processed


def _iter_audio_files(
    *,
    root: Path,
) -> Iterable[Path]:
    yield from sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES
        ),
        key=lambda path: path.as_posix(),
    )


def _sha256(
    *,
    path: Path,
) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _duration_seconds(
    *,
    path: Path,
) -> float:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as audio:
            return round(audio.getnframes() / audio.getframerate(), 3)
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Cannot obtain duration for {path}; install FFmpeg (ffprobe).")
    try:
        return round(float(result.stdout.strip()), 3)
    except ValueError as error:
        raise RuntimeError(f"ffprobe returned no duration for {path}.") from error


def _hero_name(
    *,
    audio_id: str,
    pattern: str | None,
) -> str:
    normalized = audio_id.replace("\\", "/")
    if pattern:
        match = re.search(pattern, normalized)
        if match is None or match.groupdict().get("hero") is None:
            raise ValueError("--hero-regex must match every audio path and contain (?P<hero>...).")
        return match.group("hero")
    parts = Path(normalized).parts
    labels = {"hero", "heroes", "character", "characters", "npc", "vo", "voice"}
    for index, part in enumerate(parts[:-1]):
        if part.casefold() in labels and index + 1 < len(parts) - 1:
            return parts[index + 1]
    return Path(normalized).parent.name or "unknown"


def _safe_filename(
    *,
    value: str,
) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._") or "unknown"


def _load_existing(
    *,
    path: Path,
) -> dict[str, Transcription]:
    entries: dict[str, Transcription] = {}
    if not path.exists():
        return entries
    with path.open(encoding="utf-8") as file:
        raw_entries = json.load(file)
    if not isinstance(raw_entries, list):
        return entries
    for raw in raw_entries:
        if not isinstance(raw, dict) or not isinstance(raw.get("hash"), str):
            continue
        try:
            entries[raw["hash"]] = Transcription(
                id=str(raw["id"]),
                hash=raw["hash"],
                text=_language_text_from_raw(raw=raw),
                duration=float(raw["duration"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
    return entries


def _migrate_misgrouped_entries(
    *,
    output_dir: Path,
    hero_pattern: str | None,
) -> None:
    migrated_entries: defaultdict[str, list[Transcription]] = defaultdict(list)
    source_entries: dict[Path, list[Transcription]] = {}
    for source_path in output_dir.glob("*.json"):
        entries = list(_load_existing(path=source_path).values())
        if entries:
            source_entries[source_path] = entries
    for source_path, entries in source_entries.items():
        retained_entries: list[Transcription] = []
        for entry in entries:
            hero = _hero_name(audio_id=entry.id, pattern=hero_pattern)
            target_path = output_dir / f"{_safe_filename(value=hero)}.json"
            if target_path == source_path:
                retained_entries.append(entry)
            else:
                migrated_entries[hero].append(entry)
        source_entries[source_path] = retained_entries
    for hero, entries in migrated_entries.items():
        target = output_dir / f"{_safe_filename(value=hero)}.json"
        existing = _load_existing(path=target)
        existing.update({entry.hash: entry for entry in entries})
        _write_entries(path=target, entries=sorted(existing.values(), key=lambda item: item.id))
    for source_path, entries in source_entries.items():
        if entries:
            _write_entries(path=source_path, entries=sorted(entries, key=lambda item: item.id))
        else:
            source_path.unlink()


def _write_entries(
    *,
    path: Path,
    entries: list[Transcription],
) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump([entry.as_dict() for entry in entries], file, ensure_ascii=False, indent=2)
        file.write("\n")


def _meta_from_raw(
    *,
    raw: dict[object, object],
) -> dict[str, str] | None:
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        return None
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in meta.items()):
        return None
    return dict(meta)


def _language_text_from_raw(
    *,
    raw: dict[object, object],
) -> dict[str, LanguageText]:
    raw_text = raw["text"]
    if not isinstance(raw_text, dict):
        raise ValueError("Text must be an object")
    legacy_english_text = raw_text.get("en")
    if isinstance(legacy_english_text, str):
        return {
            "en": LanguageText(
                text=legacy_english_text,
                source=Source(raw["source"]),
                meta=_meta_from_raw(raw=raw) or {},
            )
        }
    text: dict[str, LanguageText] = {}
    for language, raw_language_text in raw_text.items():
        if not isinstance(language, str) or not isinstance(raw_language_text, dict):
            continue
        value = raw_language_text.get("text")
        if not isinstance(value, str):
            continue
        text[language] = LanguageText(
            text=value,
            source=Source(raw_language_text["source"]),
            meta=_meta_from_raw(raw=raw_language_text) or {},
        )
    if not text:
        raise ValueError("Text must contain at least one language")
    return text
