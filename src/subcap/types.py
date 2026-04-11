from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class SubtitleEntry:
    start: float
    end: float
    text: str
