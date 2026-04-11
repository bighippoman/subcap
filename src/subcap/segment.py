from __future__ import annotations

from subcap.types import SubtitleEntry, Word

_SENTENCE_ENDS = frozenset(".?!")
_MAX_DURATION = 8.0
_GAP = 0.12


def _is_sentence_end(word: str) -> bool:
    return word[-1] in _SENTENCE_ENDS if word else False


def _wrap_lines(words: list[str], max_chars: int) -> str:
    """Pack words into lines of at most *max_chars*, joined with \\N."""
    lines: list[str] = []
    current: list[str] = []
    length = 0

    for w in words:
        added = len(w) if length == 0 else len(w) + 1
        if current and length + added > max_chars:
            lines.append(" ".join(current))
            current = [w]
            length = len(w)
        else:
            current.append(w)
            length += added

    if current:
        lines.append(" ".join(current))
    return "\\N".join(lines)


def _line_count(words: list[str], max_chars: int) -> int:
    """How many lines would these words occupy when wrapped?"""
    if not words:
        return 0
    count = 1
    length = 0
    for w in words:
        added = len(w) if length == 0 else len(w) + 1
        if length > 0 and length + added > max_chars:
            count += 1
            length = len(w)
        else:
            length += added
    return count


def segment_words(
    words: list[Word],
    *,
    max_chars: int,
    max_lines: int,
) -> list[SubtitleEntry]:
    if not words:
        return []

    entries: list[SubtitleEntry] = []
    buf: list[Word] = []

    def flush() -> None:
        if not buf:
            return
        if max_lines == 1:
            text = " ".join(w.text for w in buf)
        else:
            text = _wrap_lines([w.text for w in buf], max_chars)
        entries.append(SubtitleEntry(
            start=buf[0].start,
            end=buf[-1].end,
            text=text,
        ))
        buf.clear()

    for word in words:
        # Check if adding this word would overflow the subtitle.
        candidate = [w.text for w in buf] + [word.text]
        would_overflow = _line_count(candidate, max_chars) > max_lines
        duration_with = word.end - buf[0].start if buf else 0.0
        would_timeout = buf and duration_with > _MAX_DURATION

        if would_overflow or would_timeout:
            flush()

        buf.append(word)

        if _is_sentence_end(word.text):
            flush()

    flush()
    return entries
