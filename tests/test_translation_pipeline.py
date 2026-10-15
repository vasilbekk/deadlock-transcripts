"""
Tests for Russian translation catalogue updates
"""

import json
from pathlib import Path

from deadlock_transcriptor.models import Source
from deadlock_translator.pipeline import translate_catalogue


def test_translate_catalogue_adds_selected_language_and_skips_existing_entries(
    tmp_path: Path,
) -> None:
    """
    English entries without selected-language text must be translated once
    """
    path = tmp_path / "orion.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "sounds/vo/orion/line.mp3",
                    "hash": "hash",
                    "text": {
                        "en": {"text": "Grey Talon is here", "source": "whisper", "meta": {}},
                        "ru": {"text": "Существующий перевод", "source": "manual", "meta": {}},
                    },
                    "duration": 1.0,
                },
                {
                    "id": "sounds/vo/orion/line_02.mp3",
                    "hash": "second-hash",
                    "text": {
                        "en": {"text": "Grey Talon is ready", "source": "whisper", "meta": {}}
                    },
                    "duration": 1.0,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def translate(
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        assert text == "Grey Talon is ready"
        assert language == "ru"
        assert record_id == "sounds/vo/orion/line_02.mp3"
        assert glossary_prompt == ""
        return "Серый Сокол готов"

    translated = translate_catalogue(
        input_dir=tmp_path,
        translate=translate,
        model="qwen2.5:7b",
    )

    assert translated == 1
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert entries[0]["text"]["ru"]["text"] == "Существующий перевод"
    assert entries[1]["text"]["ru"] == {
        "text": "Серый Сокол готов",
        "source": Source.QWEN_OLLAMA,
        "meta": {"model": "qwen2.5:7b"},
    }


def test_translate_catalogue_writes_the_requested_language_key(
    tmp_path: Path,
) -> None:
    """
    A non-Russian language must be stored under its requested language key
    """
    path = tmp_path / "orion.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": "sounds/vo/orion/line.mp3",
                    "hash": "hash",
                    "text": {"en": {"text": "Grey Talon is here", "source": "whisper", "meta": {}}},
                    "duration": 1.0,
                }
            ]
        ),
        encoding="utf-8",
    )

    def translate(
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        assert language == "de"
        return "Grey Talon ist hier"

    translate_catalogue(
        input_dir=tmp_path,
        translate=translate,
        model="qwen2.5:7b",
        language="de",
    )

    entries = json.loads(path.read_text(encoding="utf-8"))
    assert entries[0]["text"]["de"]["text"] == "Grey Talon ist hier"


def test_translate_catalogue_limits_work_to_selected_heroes(
    tmp_path: Path,
) -> None:
    """
    Only explicitly selected hero files must be changed
    """
    for hero in ("orion", "haze"):
        (tmp_path / f"{hero}.json").write_text(
            json.dumps(
                [
                    {
                        "id": f"sounds/vo/{hero}/line.mp3",
                        "hash": hero,
                        "text": {"en": {"text": hero, "source": "whisper", "meta": {}}},
                        "duration": 1.0,
                    }
                ]
            ),
            encoding="utf-8",
        )

    def translate(
        *,
        text: str,
        language: str,
        record_id: str,
        glossary_prompt: str,
    ) -> str:
        return f"translated {text}"

    translate_catalogue(
        input_dir=tmp_path,
        translate=translate,
        model="qwen3:14b",
        heroes=frozenset({"orion"}),
    )

    orion_entries = json.loads((tmp_path / "orion.json").read_text(encoding="utf-8"))
    haze_entries = json.loads((tmp_path / "haze.json").read_text(encoding="utf-8"))
    assert orion_entries[0]["text"]["ru"]["text"] == "translated orion"
    assert "ru" not in haze_entries[0]["text"]
