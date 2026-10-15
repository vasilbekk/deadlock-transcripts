"""
Command-line interface for translating Deadlock transcriptions with Ollama
"""

import argparse
from pathlib import Path

from deadlock_translator.game_localization import load_game_localization
from deadlock_translator.glossary import load_translation_glossary
from deadlock_translator.ollama import OllamaTranslator
from deadlock_translator.pipeline import translate_catalogue
from deadlock_translator.progress import TranslationProgressReporter


def main() -> None:
    """
    Translate English transcript records into a selected language with Ollama
    """
    arguments = _build_parser().parse_args()
    translator = OllamaTranslator(model=arguments.model, endpoint=arguments.endpoint)
    glossary = load_translation_glossary(
        path=arguments.glossary_file
        or Path(f"data/translation-glossary.{arguments.language.casefold()}.json")
    )
    localization_path = arguments.game_localization_file
    if localization_path is None and arguments.language.casefold() == "ru":
        localization_path = Path("data/citadel_generated_vo_russian.txt")
    game_localization_tokens = load_game_localization(path=localization_path)
    translated = translate_catalogue(
        input_dir=arguments.input_dir,
        translate=lambda *, text, language, record_id, glossary_prompt: translator.translate(
            text=text,
            language=language,
            record_id=record_id,
            glossary_prompt=glossary_prompt,
        ),
        model=arguments.model,
        language=arguments.language,
        glossary=glossary,
        game_localization_tokens=game_localization_tokens,
        heroes=frozenset(hero.casefold() for hero in arguments.hero),
        overwrite=arguments.overwrite,
        progress=TranslationProgressReporter(),
    )
    print(f"Translated {translated} transcript entries.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate Deadlock transcript JSON files into a selected language with Ollama."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing hero JSON files.")
    parser.add_argument("--model", default="qwen2.5:7b", help="Installed Ollama model name.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434", help="Ollama URL.")
    parser.add_argument(
        "--language",
        default="ru",
        help="Target ISO language code written under text.<language>.",
    )
    parser.add_argument(
        "--hero",
        action="append",
        default=[],
        help="Hero JSON filename to translate; repeat this option for multiple heroes.",
    )
    parser.add_argument(
        "--game-localization-file",
        type=Path,
        help="Official Valve localization file checked before Ollama.",
    )
    parser.add_argument(
        "--glossary-file",
        type=Path,
        help="Optional terminology glossary JSON file for the target language.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing text in the selected target language.",
    )
    return parser
