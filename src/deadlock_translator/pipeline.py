"""
Translation pipeline for generated Deadlock transcription JSON files
"""

import json
from pathlib import Path
from typing import Any, Protocol

from deadlock_transcriptor.models import Source
from deadlock_translator.game_localization import find_game_translation
from deadlock_translator.glossary import TranslationGlossary
from deadlock_translator.progress import TranslationProgressReporter


class Translator(Protocol):
    """
    Callable that translates one English line into a requested language
    """

    def __call__(
        self,
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        """
        Translate the supplied English text into the requested language
        """


def translate_catalogue(
    *,
    input_dir: Path,
    translate: Translator,
    model: str,
    language: str = "ru",
    glossary: TranslationGlossary | None = None,
    game_localization_tokens: dict[str, str] | None = None,
    heroes: frozenset[str] | None = None,
    overwrite: bool = False,
    progress: TranslationProgressReporter | None = None,
) -> int:
    """
    Add translations in the requested language to every eligible transcript entry
    """
    paths = _select_hero_paths(
        paths=sorted(input_dir.glob("*.json")),
        heroes=heroes,
    )
    if progress:
        progress.start(total=_count_candidates(paths=paths, language=language, overwrite=overwrite))
    translated = 0
    for path in paths:
        translated += translate_file(
            path=path,
            translate=translate,
            model=model,
            language=language,
            glossary=glossary,
            game_localization_tokens=game_localization_tokens,
            overwrite=overwrite,
            progress=progress,
        )
    if progress:
        progress.finish()
    return translated


def _select_hero_paths(
    *,
    paths: list[Path],
    heroes: frozenset[str] | None,
) -> list[Path]:
    """
    Return only requested hero files and reject names without a JSON file
    """
    if not heroes:
        return paths
    available_heroes = {path.stem.casefold() for path in paths}
    missing_heroes = sorted(heroes - available_heroes)
    if missing_heroes:
        raise ValueError(f"Hero JSON files not found: {', '.join(missing_heroes)}")
    return [path for path in paths if path.stem.casefold() in heroes]


def translate_file(
    *,
    path: Path,
    translate: Translator,
    model: str,
    language: str,
    glossary: TranslationGlossary | None,
    game_localization_tokens: dict[str, str] | None,
    overwrite: bool,
    progress: TranslationProgressReporter | None = None,
) -> int:
    """
    Add translations in the requested language to one hero JSON file
    """
    with path.open(encoding="utf-8") as file:
        payload: Any = json.load(file)
    if not isinstance(payload, list):
        return 0
    translated = 0
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        source_text = _source_text(entry=entry)
        if source_text is None or not _should_translate(
            entry=entry,
            language=language,
            overwrite=overwrite,
        ):
            continue
        text = entry["text"]
        record_id = str(entry.get("id", ""))
        game_translation = find_game_translation(
            record_id=record_id,
            tokens=game_localization_tokens or {},
        )
        if game_translation:
            translated_text, token = game_translation
            source = Source.ORIGINAL
            meta = {"token": token}
            if progress:
                progress.localized(record_id=record_id, source_text=source_text)
        else:
            if progress:
                progress.translating(record_id=record_id, source_text=source_text)
            translated_text = translate(
                text=source_text,
                language=language,
                record_id=record_id,
                glossary_prompt=glossary.prompt() if glossary else "",
            ).strip()
            if glossary:
                translated_text = glossary.apply(text=translated_text)
            source = Source.QWEN_OLLAMA
            meta = {"model": model}
        if not translated_text:
            continue
        text[language] = {
            "text": translated_text,
            "source": source,
            "meta": meta,
        }
        translated += 1
        if progress:
            progress.translated(language=language, translated_text=translated_text)
            progress.update()
    if translated:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
    return translated


def _count_candidates(
    *,
    paths: list[Path],
    language: str,
    overwrite: bool,
) -> int:
    """
    Return the number of entries that require translation
    """
    total = 0
    for path in paths:
        with path.open(encoding="utf-8") as file:
            payload: Any = json.load(file)
        if isinstance(payload, list):
            total += sum(
                _should_translate(entry=entry, language=language, overwrite=overwrite)
                for entry in payload
                if isinstance(entry, dict)
            )
    return total


def _source_text(
    *,
    entry: dict[str, Any],
) -> str | None:
    """
    Return non-empty English text from a transcription entry
    """
    text = entry.get("text")
    if not isinstance(text, dict):
        return None
    english = text.get("en")
    if not isinstance(english, dict):
        return None
    source_text = english.get("text")
    return source_text if isinstance(source_text, str) and source_text.strip() else None


def _should_translate(
    *,
    entry: dict[str, Any],
    language: str,
    overwrite: bool,
) -> bool:
    """
    Return whether an entry has English text and needs the target language
    """
    if _source_text(entry=entry) is None:
        return False
    text = entry.get("text")
    if not isinstance(text, dict):
        return False
    target_text = text.get(language)
    return (
        overwrite
        or not isinstance(target_text, dict)
        or not str(target_text.get("text", "")).strip()
    )
