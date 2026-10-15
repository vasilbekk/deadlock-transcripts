"""
Console progress reporting for transcription catalogue generation
"""

import sys
import time
from collections import Counter
from enum import IntEnum
from typing import TextIO

from deadlock_transcriptor.models import Source


class ProgressBarWidth(IntEnum):
    """
    Display width of the console progress bar
    """

    DEFAULT = 24


class ProgressReporter:
    """
    Render processing progress and source statistics to a text stream
    """

    def __init__(
        self,
        *,
        stream: TextIO = sys.stderr,
        width: int = ProgressBarWidth.DEFAULT,
    ) -> None:
        self._stream = stream
        self._width = width
        self._completed = 0
        self._total = 0
        self._reused = 0
        self._sources: Counter[Source] = Counter()
        self._started_at: float | None = None
        self._hero_name: str | None = None
        self._hero_index = 0
        self._hero_total = 0
        self._rendered_line_length = 0

    def start(
        self,
        *,
        total: int,
        hero_total: int = 0,
    ) -> None:
        """
        Start progress reporting for the supplied number of audio files
        """
        self._total = total
        self._hero_total = hero_total
        self._started_at = time.monotonic()
        self._render()

    def start_hero(
        self,
        *,
        hero_name: str,
        hero_index: int,
    ) -> None:
        """
        Set the hero currently being processed
        """
        self._hero_name = hero_name
        self._hero_index = hero_index
        self._render()

    def transcribing(
        self,
        *,
        audio_id: str,
    ) -> None:
        """
        Print the audio file being sent to Whisper
        """
        print(file=self._stream)
        print(f"Transcribing: {audio_id}", file=self._stream, flush=True)

    def transcribed(
        self,
        *,
        audio_id: str,
        text: str,
    ) -> None:
        """
        Print the final Whisper text for an audio file
        """
        print(f"Transcribed: {audio_id}", file=self._stream)
        print(f"Text: {text}", file=self._stream, flush=True)

    def update(
        self,
        *,
        source: Source,
        reused: bool,
    ) -> None:
        """
        Record one completed audio file and refresh the progress bar
        """
        self._completed += 1
        self._sources[source] += 1
        if reused:
            self._reused += 1
        self._render()

    def finish(
        self,
    ) -> None:
        """
        Complete progress reporting and print the processing summary
        """
        self._render()
        elapsed = self._elapsed_seconds()
        print(file=self._stream)
        print(
            "Completed "
            f"{self._completed}/{self._total} in {_format_duration(seconds=elapsed)} | "
            f"catalogue: {self._sources[Source.MCALLBOSCO_DEADLOCK_TRANSCIPTIONS]}, "
            f"subtitles: {self._sources[Source.SUBTITLE]}, "
            f"Whisper: {self._sources[Source.WHISPER]}, reused: {self._reused}",
            file=self._stream,
            flush=True,
        )

    def _render(
        self,
    ) -> None:
        elapsed = self._elapsed_seconds()
        percentage = (self._completed / self._total * 100) if self._total else 100.0
        filled = round(self._width * percentage / 100)
        bar = f"{'#' * filled}{'-' * (self._width - filled)}"
        eta = self._eta_seconds(elapsed=elapsed)
        hero_progress = ""
        if self._hero_name is not None:
            hero_progress = f" | hero: {self._hero_name} ({self._hero_index}/{self._hero_total})"
        line = (
            f"[{bar}] {self._completed}/{self._total} ({percentage:5.1f}%) "
            f"| ETA: {_format_duration(seconds=eta)}{hero_progress}"
        )
        padding = " " * max(0, self._rendered_line_length - len(line))
        print(
            f"\r{line}{padding}",
            end="",
            file=self._stream,
            flush=True,
        )
        self._rendered_line_length = len(line)

    def _elapsed_seconds(
        self,
    ) -> float:
        if self._started_at is None:
            return 0.0
        return time.monotonic() - self._started_at

    def _eta_seconds(
        self,
        *,
        elapsed: float,
    ) -> float:
        if self._completed == 0:
            return 0.0
        return elapsed / self._completed * (self._total - self._completed)


def _format_duration(
    *,
    seconds: float,
) -> str:
    total_seconds = round(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
