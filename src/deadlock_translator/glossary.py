"""
Terminology glossary support for translation models
"""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class GlossaryField(StrEnum):
    """
    JSON field names for a translation glossary
    """

    REPLACEMENTS = "replacements"
    TERMS = "terms"


@dataclass(frozen=True, slots=True)
class TranslationGlossary:
    """
    Locked target-language terminology and deterministic corrections
    """

    terms: dict[str, str] = field(default_factory=dict)
    replacements: dict[str, str] = field(default_factory=dict)

    def prompt(
        self,
    ) -> str:
        """
        Render terminology instructions for the translation model
        """
        if not self.terms:
            return ""
        entries = "\n".join(f"- {source} → {target}" for source, target in self.terms.items())
        return (
            "Locked terminology\n"
            f"{entries}\n"
            "Use the listed target-language form or its grammatically correct inflection\n"
            "Never replace a listed name with a similar-sounding name\n"
        )

    def apply(
        self,
        *,
        text: str,
    ) -> str:
        """
        Apply deterministic corrections to a model translation
        """
        corrected = text
        for source, target in self.replacements.items():
            corrected = corrected.replace(source, target)
        return corrected


def load_translation_glossary(
    *,
    path: Path | None,
) -> TranslationGlossary:
    """
    Load an optional language-specific translation glossary
    """
    if path is None or not path.is_file():
        return TranslationGlossary()
    with path.open(encoding="utf-8") as file:
        payload: object = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"Translation glossary must be a JSON object: {path}")
    return TranslationGlossary(
        terms=_read_mapping(payload=payload, field=GlossaryField.TERMS, path=path),
        replacements=_read_mapping(payload=payload, field=GlossaryField.REPLACEMENTS, path=path),
    )


def _read_mapping(
    *,
    payload: dict[object, object],
    field: GlossaryField,
    path: Path,
) -> dict[str, str]:
    value = payload.get(field, {})
    if not isinstance(value, dict) or not all(
        isinstance(source, str) and isinstance(target, str) for source, target in value.items()
    ):
        raise ValueError(f"Glossary '{field}' must map strings to strings: {path}")
    return dict(value)
