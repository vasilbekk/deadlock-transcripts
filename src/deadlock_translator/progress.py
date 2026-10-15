"""
Console progress reporting for translation generation
"""

import sys
import time
from enum import IntEnum
from typing import TextIO


class ProgressBarWidth(IntEnum):
    """
    Display width of the console progress bar
    """

    DEFAULT = 24


class TranslationProgressReporter:
    """
    Render translation progress and English-to-target-language logs
    """

    def __init__(
        self,
        *,
        stream: TextIO = sys.stderr,
        width: int = ProgressBarWidth.DEFAULT,
    ) -> None:
        """
        Initialize an empty translation progress display
        """
        self._stream = stream
        self._width = width
        self._completed = 0
        self._total = 0
        self._started_at: float | None = None
        self._rendered_line_length = 0

    def start(
        self,
        *,
        total: int,
    ) -> None:
        """
        Start reporting progress for the supplied number of translations
        """
        self._total = total
        self._started_at = time.monotonic()
        self._render()

    def translating(
        self,
        *,
        record_id: str,
        source_text: str,
    ) -> None:
        """
        Print the English voice line being sent to the translator
        """
        print(file=self._stream)
        print(f"Translating: {record_id}", file=self._stream)
        print(f"English: {source_text}", file=self._stream, flush=True)

    def translated(
        self,
        *,
        language: str,
        translated_text: str,
    ) -> None:
        """
        Print the completed target-language text
        """
        print(f"Translation ({language}): {translated_text}", file=self._stream, flush=True)

    def localized(
        self,
        *,
        record_id: str,
        source_text: str,
    ) -> None:
        """
        Print the English line resolved from official game localization
        """
        print(file=self._stream)
        print(f"Using game localization: {record_id}", file=self._stream)
        print(f"English: {source_text}", file=self._stream, flush=True)

    def update(
        self,
    ) -> None:
        """
        Record a completed translation and refresh the progress bar
        """
        self._completed += 1
        self._render()

    def finish(
        self,
    ) -> None:
        """
        Finish reporting progress
        """
        self._render()
        print(file=self._stream, flush=True)

    def _render(
        self,
    ) -> None:
        elapsed = self._elapsed_seconds()
        percentage = self._completed / self._total * 100 if self._total else 100.0
        filled = round(self._width * percentage / 100)
        bar = f"{'#' * filled}{'-' * (self._width - filled)}"
        line = (
            f"[{bar}] {self._completed}/{self._total} ({percentage:5.1f}%) "
            f"| ETA: {_format_duration(seconds=self._eta_seconds(elapsed=elapsed))}"
        )
        padding = " " * max(0, self._rendered_line_length - len(line))
        print(f"\r{line}{padding}", end="", file=self._stream, flush=True)
        self._rendered_line_length = len(line)

    def _elapsed_seconds(
        self,
    ) -> float:
        """
        Return elapsed monotonic seconds since reporting started
        """
        return time.monotonic() - self._started_at if self._started_at else 0.0

    def _eta_seconds(
        self,
        *,
        elapsed: float,
    ) -> float:
        """
        Return the estimated seconds until completion
        """
        if self._completed == 0:
            return 0.0
        return elapsed / self._completed * (self._total - self._completed)


def _format_duration(
    *,
    seconds: float,
) -> str:
    """
    Format seconds as a console duration
    """
    total_seconds = round(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
