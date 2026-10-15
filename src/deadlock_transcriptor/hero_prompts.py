"""
Hero-specific context prompts for Whisper transcription
"""

import json
from enum import StrEnum
from pathlib import Path


class HeroPromptField(StrEnum):
    """
    JSON field names for the hero prompt file
    """

    HEROES = "heroes"


def load_hero_prompts(
    *,
    path: Path,
    initial_prompt: str | None,
) -> dict[str, str]:
    """
    Load one concise Whisper prompt for each hero code
    """
    base_prompt = initial_prompt.strip() if initial_prompt else ""
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as file:
        payload: object = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Hero prompt file must be a JSON object: {path}")
    raw_heroes = payload.get(HeroPromptField.HEROES)
    if not isinstance(raw_heroes, dict):
        raise ValueError(f"Hero prompt file must contain '{HeroPromptField.HEROES}': {path}")
    prompts: dict[str, str] = {}
    for hero, raw_names in raw_heroes.items():
        if not isinstance(hero, str) or not isinstance(raw_names, list):
            raise ValueError(f"Hero prompt names must be a list of strings: {path}")
        names = [name.strip() for name in raw_names if isinstance(name, str) and name.strip()]
        if not names:
            continue
        hero_prompt = (
            "This is an English voice line from the game Deadlock. "
            f"Relevant character names: {', '.join(dict.fromkeys(names))}."
        )
        prompts[hero.casefold()] = " ".join(part for part in (base_prompt, hero_prompt) if part)
    return prompts
