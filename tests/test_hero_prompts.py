"""
Tests for hero-specific Whisper context prompts
"""

import json
from pathlib import Path

from deadlock_transcriptor.hero_prompts import load_hero_prompts


def test_load_hero_prompts_includes_display_and_code_names(
    tmp_path: Path,
) -> None:
    """
    Hero aliases must be supplied to Whisper as one short prompt
    """
    path = tmp_path / "hero-prompts.json"
    path.write_text(
        json.dumps({"heroes": {"orion": ["Grey Talon", "Orion"]}}),
        encoding="utf-8",
    )

    prompts = load_hero_prompts(
        path=path,
        initial_prompt="Deadlock dialogue",
    )

    assert prompts == {
        "orion": (
            "Deadlock dialogue This is an English voice line from the game Deadlock. "
            "Relevant character names: Grey Talon, Orion."
        )
    }
