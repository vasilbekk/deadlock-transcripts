"""
Tests for catalogue assembly without downloading a Whisper model
"""

import json
import wave
from io import StringIO
from pathlib import Path

from deadlock_transcriptor.models import Source
from deadlock_transcriptor.pipeline import build_catalogue
from deadlock_transcriptor.progress import ProgressReporter


def test_build_catalogue_prefers_subtitle_and_groups_by_hero(
    tmp_path: Path,
) -> None:
    """
    Subtitle-backed audio must not be passed to Whisper
    """
    audio_dir = tmp_path / "game" / "heroes" / "Kelvin"
    audio_dir.mkdir(parents=True)
    audio_path = audio_dir / "hello.wav"
    _write_silent_wav(path=audio_path)
    (tmp_path / "game" / "subtitles.json").write_text(
        json.dumps({"heroes/Kelvin/hello.wav": "Hello, <i>friend</i>."}), encoding="utf-8"
    )
    output_dir = tmp_path / "transcriptions"

    def should_not_transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        raise AssertionError(f"Whisper was called for {audio_path}")

    processed = build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=output_dir,
        transcribe=should_not_transcribe,
        whisper_model="test-model",
    )

    assert processed == 1
    entries = json.loads((output_dir / "Kelvin.json").read_text(encoding="utf-8"))
    assert entries[0]["id"] == "heroes/Kelvin/hello.wav"
    assert entries[0]["text"] == {
        "en": {
            "text": "Hello, friend.",
            "source": "subtitle",
            "meta": {},
        }
    }
    assert entries[0]["duration"] == 0.1


def test_build_catalogue_transcribes_missing_subtitle_once(
    tmp_path: Path,
) -> None:
    """
    A hash already in output prevents a second transcription
    """
    audio_dir = tmp_path / "game" / "vo" / "Lady_Geist"
    audio_dir.mkdir(parents=True)
    _write_silent_wav(path=audio_dir / "missing.wav")
    output_dir = tmp_path / "transcriptions"

    def transcribe_once(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        assert audio_path.name == "missing.wav"
        return "A new line."

    def should_not_transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        raise AssertionError(f"Whisper was called twice for {audio_path}")

    first = build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=output_dir,
        transcribe=transcribe_once,
        whisper_model="test-model",
    )
    second = build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=output_dir,
        transcribe=should_not_transcribe,
        whisper_model="test-model",
    )

    assert first == 1
    assert second == 0
    entries = json.loads((output_dir / "Lady_Geist.json").read_text(encoding="utf-8"))
    assert entries[0]["text"]["en"]["source"] == "whisper"
    assert entries[0]["text"]["en"]["meta"] == {"model": "test-model"}


def test_build_catalogue_passes_the_current_hero_prompt_to_whisper(
    tmp_path: Path,
) -> None:
    """
    Whisper must receive context for the hero currently being processed
    """
    audio_dir = tmp_path / "game" / "sounds" / "vo" / "orion"
    audio_dir.mkdir(parents=True)
    _write_silent_wav(path=audio_dir / "line.wav")

    def transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        assert initial_prompt == "Relevant character names: Grey Talon, Orion."
        return "Grey Talon line"

    build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=tmp_path / "transcriptions",
        transcribe=transcribe,
        whisper_model="test-model",
        hero_prompts={"orion": "Relevant character names: Grey Talon, Orion."},
    )


def test_build_catalogue_migrates_a_legacy_cached_entry(
    tmp_path: Path,
) -> None:
    """
    Legacy root source and meta fields must move into the English text record
    """
    audio_dir = tmp_path / "game" / "heroes" / "Kelvin"
    audio_dir.mkdir(parents=True)
    _write_silent_wav(path=audio_dir / "hello.wav")
    output_dir = tmp_path / "transcriptions"
    output_dir.mkdir()
    (output_dir / "Kelvin.json").write_text(
        json.dumps(
            [
                {
                    "id": "heroes/Kelvin/hello.wav",
                    "hash": "f267e2c3a2079731f38479c5a32998dc7e0099418a96f88c7163b3287547c07a",
                    "source": "subtitle",
                    "text": {"en": "Legacy line."},
                    "duration": 0.1,
                    "meta": {"origin": "old-schema"},
                }
            ]
        ),
        encoding="utf-8",
    )

    def should_not_transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        raise AssertionError(f"Whisper was called for {audio_path}")

    processed = build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=output_dir,
        transcribe=should_not_transcribe,
        whisper_model="test-model",
    )

    assert processed == 0
    entries = json.loads((output_dir / "Kelvin.json").read_text(encoding="utf-8"))
    assert entries[0]["text"] == {
        "en": {
            "text": "Legacy line.",
            "source": "subtitle",
            "meta": {"origin": "old-schema"},
        }
    }
    assert "source" not in entries[0]
    assert "meta" not in entries[0]


def test_build_catalogue_uses_external_transcript_catalogue(
    tmp_path: Path,
) -> None:
    """
    A matching external transcript must be used before Whisper
    """
    audio_dir = tmp_path / "game" / "sounds" / "vo" / "Kelvin"
    audio_dir.mkdir(parents=True)
    audio_path = audio_dir / "hello.wav"
    _write_silent_wav(path=audio_path)
    digest = "f267e2c3a2079731f38479c5a32998dc7e0099418a96f88c7163b3287547c07a"
    catalogue_dir = tmp_path / "catalogue" / "Kelvin"
    catalogue_dir.mkdir(parents=True)
    (catalogue_dir / "line.json").write_text(
        json.dumps(
            {
                "schemaVersion": 3,
                "filename": "kelvin/hello.wav",
                "revisions": [
                    {
                        "sha256": [digest],
                        "text": "Already transcribed.",
                        "source": "official",
                        "model": "manual-review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def should_not_transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        raise AssertionError(f"Whisper was called for {audio_path}")

    build_catalogue(
        input_dir=tmp_path / "game",
        output_dir=tmp_path / "transcriptions",
        transcribe=should_not_transcribe,
        whisper_model="test-model",
        transcript_dirs=(catalogue_dir.parent,),
    )

    entries = json.loads((tmp_path / "transcriptions" / "Kelvin.json").read_text())
    assert entries[0]["text"] == {
        "en": {
            "text": "Already transcribed.",
            "source": "mcallbosco-deadlock-transciptions",
            "meta": {
                "schema_version": "3",
                "filename": "kelvin/hello.wav",
                "source": "official",
                "model": "manual-review",
            },
        }
    }


def test_progress_reporter_prints_completion_eta_and_current_hero() -> None:
    """
    Progress reporting must include completion, ETA, and the current hero
    """
    stream = StringIO()
    reporter = ProgressReporter(stream=stream, width=10)

    reporter.start(total=2, hero_total=1)
    reporter.start_hero(hero_name="Kelvin", hero_index=1)
    reporter.transcribing(audio_id="heroes/Kelvin/hello.wav")
    reporter.transcribed(
        audio_id="heroes/Kelvin/hello.wav",
        text="Hello, friend.",
    )
    reporter.update(source=Source.SUBTITLE, reused=False)
    reporter.update(source=Source.WHISPER, reused=False)
    reporter.finish()

    output = stream.getvalue()
    assert "2/2 (100.0%)" in output
    assert "ETA: 00:00" in output
    assert "hero: Kelvin (1/1)" in output
    assert "Transcribing: heroes/Kelvin/hello.wav" in output
    assert "Text: Hello, friend." in output


def test_progress_reporter_clears_the_tail_of_a_shorter_hero_count() -> None:
    """
    A shorter hero count must not retain characters from the previous line
    """
    stream = StringIO()
    reporter = ProgressReporter(stream=stream, width=10)

    reporter.start(total=1, hero_total=500)
    reporter.start_hero(hero_name="Baba", hero_index=4)
    reporter.start(total=1, hero_total=53)
    reporter.start_hero(hero_name="Baba", hero_index=4)

    output = stream.getvalue()
    assert "hero: Baba (4/53) " in output
    assert "hero: Baba (4/530)" not in output
    assert "hero: Baba (4/500)" in output


def test_build_catalogue_writes_a_hero_before_starting_the_next_one(
    tmp_path: Path,
) -> None:
    """
    Each hero file must exist before transcription begins for the next hero
    """
    input_dir = tmp_path / "game"
    kelvin_audio = input_dir / "heroes" / "Kelvin" / "hello.wav"
    haze_audio = input_dir / "heroes" / "Haze" / "hello.wav"
    kelvin_audio.parent.mkdir(parents=True)
    haze_audio.parent.mkdir(parents=True)
    _write_silent_wav(path=kelvin_audio)
    _write_silent_wav(path=haze_audio)
    output_dir = tmp_path / "transcriptions"

    def transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        if audio_path.parent.name == "Haze":
            return "Haze line"
        assert (output_dir / "Haze.json").exists()
        return "Kelvin line"

    build_catalogue(
        input_dir=input_dir,
        output_dir=output_dir,
        transcribe=transcribe,
        whisper_model="test-model",
    )

    assert (output_dir / "Haze.json").exists()
    assert (output_dir / "Kelvin.json").exists()


def test_build_catalogue_groups_emote_audio_with_its_hero(
    tmp_path: Path,
) -> None:
    """
    An emote subdirectory must not replace the hero name from the vo path
    """
    input_dir = tmp_path / "game"
    audio_path = input_dir / "sounds" / "vo" / "Chessmaster" / "emote" / "line.wav"
    audio_path.parent.mkdir(parents=True)
    _write_silent_wav(path=audio_path)

    def transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        return "Chessmaster line"

    output_dir = tmp_path / "transcriptions"
    build_catalogue(
        input_dir=input_dir,
        output_dir=output_dir,
        transcribe=transcribe,
        whisper_model="test-model",
    )

    assert (output_dir / "Chessmaster.json").exists()
    assert not (output_dir / "emote.json").exists()


def test_build_catalogue_groups_announcer_variants_together(
    tmp_path: Path,
) -> None:
    """
    Announcer variants must be grouped under the announcer
    """
    input_dir = tmp_path / "game"
    audio_path = input_dir / "sounds" / "vo" / "announcer" / "female" / "line.wav"
    audio_path.parent.mkdir(parents=True)
    _write_silent_wav(path=audio_path)
    output_dir = tmp_path / "transcriptions"

    def transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        return "Announcer line"

    build_catalogue(
        input_dir=input_dir,
        output_dir=output_dir,
        transcribe=transcribe,
        whisper_model="test-model",
    )

    assert (output_dir / "announcer.json").exists()
    assert not (output_dir / "female.json").exists()


def test_build_catalogue_migrates_emote_entries_to_their_heroes(
    tmp_path: Path,
) -> None:
    """
    Existing emote output must move to its hero cache without Whisper work
    """
    input_dir = tmp_path / "game"
    audio_path = input_dir / "sounds" / "vo" / "Chessmaster" / "emote" / "line.wav"
    audio_path.parent.mkdir(parents=True)
    _write_silent_wav(path=audio_path)
    output_dir = tmp_path / "transcriptions"
    output_dir.mkdir()
    (output_dir / "emote.json").write_text(
        json.dumps(
            [
                {
                    "id": "sounds/vo/Chessmaster/emote/line.wav",
                    "hash": "f267e2c3a2079731f38479c5a32998dc7e0099418a96f88c7163b3287547c07a",
                    "text": {
                        "en": {
                            "text": "Cached emote.",
                            "source": "whisper",
                            "meta": {"model": "test-model"},
                        }
                    },
                    "duration": 0.1,
                }
            ]
        ),
        encoding="utf-8",
    )

    def should_not_transcribe(
        *,
        audio_path: Path,
        initial_prompt: str | None,
    ) -> str:
        raise AssertionError(f"Whisper was called for {audio_path}")

    processed = build_catalogue(
        input_dir=input_dir,
        output_dir=output_dir,
        transcribe=should_not_transcribe,
        whisper_model="test-model",
    )

    assert processed == 0
    assert not (output_dir / "emote.json").exists()
    entries = json.loads((output_dir / "Chessmaster.json").read_text(encoding="utf-8"))
    assert entries[0]["text"]["en"]["text"] == "Cached emote."


def _write_silent_wav(
    *,
    path: Path,
) -> None:
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(10)
        file.writeframes(b"\0\0")
