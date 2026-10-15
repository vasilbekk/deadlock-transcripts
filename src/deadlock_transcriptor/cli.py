"""
Command-line interface for Deadlock transcription catalogue generation
"""

import argparse
from pathlib import Path
from typing import Any

from deadlock_transcriptor.cuda import configure_cuda_libraries
from deadlock_transcriptor.hero_prompts import load_hero_prompts
from deadlock_transcriptor.pipeline import Transcriber, build_catalogue
from deadlock_transcriptor.progress import ProgressReporter


def main() -> None:
    """
    Parse command-line arguments and build the catalogue
    """
    configure_cuda_libraries()
    arguments = _build_parser().parse_args()
    transcribe = _make_transcriber(
        model=arguments.model,
        device=arguments.device,
        compute_type=arguments.compute_type,
    )
    hero_prompts = load_hero_prompts(
        path=arguments.hero_prompts_file,
        initial_prompt=arguments.initial_prompt,
    )
    processed = build_catalogue(
        input_dir=arguments.input_dir,
        output_dir=arguments.output_dir,
        transcribe=transcribe,
        whisper_model=arguments.model,
        hero_pattern=arguments.hero_regex,
        overwrite=arguments.overwrite,
        progress=ProgressReporter(),
        transcript_dirs=tuple(arguments.transcripts_dir),
        hero_prompts=hero_prompts,
    )
    print(f"Created or refreshed {processed} catalogue entries.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Deadlock voice-line transcription JSON files."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder containing extracted game audio and subtitles.",
    )
    parser.add_argument(
        "--hero-prompts-file",
        default=Path("data/hero-prompts.json"),
        type=Path,
        help="JSON file mapping hero codes to Whisper name variants.",
    )
    parser.add_argument(
        "--initial-prompt",
        help="Optional context prepended to every hero-specific Whisper prompt.",
    )
    parser.add_argument("output_dir", type=Path, help="Directory for per-hero JSON files.")
    parser.add_argument(
        "--model",
        default="large-v3",
        help="faster-whisper model name or local path.",
    )
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--compute-type", default="default")
    parser.add_argument(
        "--hero-regex",
        help="Regex with a named 'hero' group matched against audio IDs.",
    )
    parser.add_argument(
        "--transcripts-dir",
        action="append",
        default=[],
        type=Path,
        help="Directory of schema-v3 transcript JSON files to use before Whisper.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Do not reuse entries from existing output.",
    )
    return parser


def _make_transcriber(
    *,
    model: str,
    device: str,
    compute_type: str,
) -> Transcriber:
    whisper: Any | None = None

    def transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        nonlocal whisper
        if whisper is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as error:
                raise SystemExit(
                    "Missing subtitles require Whisper. "
                    "Install it with: pip install -e '.[whisper]'"
                ) from error
            whisper = WhisperModel(model, device=device, compute_type=compute_type)
        segments, _info = whisper.transcribe(
            str(audio_path),
            language="en",
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=initial_prompt,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()

    return transcribe


if __name__ == "__main__":
    main()
