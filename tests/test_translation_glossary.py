"""
Tests for translation terminology glossaries
"""

import json
from pathlib import Path

from deadlock_translator.glossary import load_translation_glossary


def test_translation_glossary_adds_prompt_terms_and_corrections(
    tmp_path: Path,
) -> None:
    """
    Locked terms must reach the model and known renderings must be corrected
    """
    path = tmp_path / "translation-glossary.ru.json"
    path.write_text(
        json.dumps(
            {
                "terms": {"Grey Talon": "Серый Коготь"},
                "replacements": {"Серый Талон": "Серый Коготь"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    glossary = load_translation_glossary(path=path)

    assert "Grey Talon → Серый Коготь" in glossary.prompt()
    assert glossary.apply(text="Серый Талон готов") == "Серый Коготь готов"
