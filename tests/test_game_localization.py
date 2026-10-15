"""
Tests for official Deadlock localization matching
"""

import json
from pathlib import Path

from deadlock_transcriptor.models import Source
from deadlock_translator.game_localization import (
    find_game_translation,
    load_game_localization,
)
from deadlock_translator.pipeline import translate_catalogue


def test_game_localization_matches_the_preferred_announcer_token(
    tmp_path: Path,
) -> None:
    """
    Official Valve tokens must match the corresponding audio filename stem
    """
    localization_path = tmp_path / "citadel_generated_vo_russian.txt"
    localization_path.write_text(
        '"line_announcer" "Официальный перевод"\n',
        encoding="utf-8",
    )

    tokens = load_game_localization(path=localization_path)

    assert find_game_translation(record_id="sounds/vo/announcer/line.mp3", tokens=tokens) == (
        "Официальный перевод",
        "line_announcer",
    )


def test_translate_catalogue_prefers_game_localization_to_ollama(
    tmp_path: Path,
) -> None:
    """
    A matched official localization must bypass the translation model
    """
    path = tmp_path / "announcer.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "sounds/vo/announcer/line.mp3",
                    "hash": "hash",
                    "text": {"en": {"text": "Official line", "source": "whisper", "meta": {}}},
                    "duration": 1.0,
                }
            ]
        ),
        encoding="utf-8",
    )

    def should_not_translate(
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        raise AssertionError("Ollama must not receive an officially localized line")

    translated = translate_catalogue(
        input_dir=tmp_path,
        translate=should_not_translate,
        model="qwen2.5:7b",
        game_localization_tokens={"line_announcer": "Официальный перевод"},
    )

    assert translated == 1
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert entries[0]["text"]["ru"] == {
        "text": "Официальный перевод",
        "source": Source.ORIGINAL,
        "meta": {"token": "line_announcer"},
    }
