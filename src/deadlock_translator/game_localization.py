"""
Readers and matchers for official Deadlock Valve localization files
"""

import re
from enum import StrEnum
from pathlib import Path


class SubtitleTokenSuffix(StrEnum):
    """
    Preferred official subtitle token suffixes
    """

    ANNOUNCER = "_announcer"
    HERO_3D = "_hero_3d"
    PING_2D = "_ping_2d"


TOKEN_LINE = re.compile(r'^\s*"(?P<key>[^"]+)"\s+"(?P<value>(?:\\.|[^"])*)"\s*$')
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def load_game_localization(
    *,
    path: Path | None,
) -> dict[str, str]:
    """
    Load non-empty official localization tokens from a Valve text file
    """
    if path is None or not path.is_file():
        return {}
    tokens: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = TOKEN_LINE.match(line)
        if match is None:
            continue
        value = (
            CONTROL_CHARACTERS.sub("", match.group("value"))
            .replace(r"\"", '"')
            .replace(r"\\", "\\")
        )
        if value:
            tokens[match.group("key")] = value
    return tokens


def find_game_translation(
    *,
    record_id: str,
    tokens: dict[str, str],
) -> tuple[str, str] | None:
    """
    Return the official text and token matching one audio record ID
    """
    stem = Path(record_id).stem
    for suffix in SubtitleTokenSuffix:
        token = f"{stem}{suffix}"
        if token in tokens:
            return tokens[token], token
    matches = sorted(token for token in tokens if token.startswith(f"{stem}_"))
    if len(matches) == 1:
        token = matches[0]
        return tokens[token], token
    return None
