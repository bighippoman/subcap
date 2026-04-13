import tempfile
from pathlib import Path

import pytest

from subcap.align import parse_srt, _recover_silences, _estimate_speech_duration
from subcap.types import SubtitleEntry, Word


# --- Silence recovery ---

def test_recover_silences_clips_stretched_word():
    # "Suggest" marked as 3s long — clearly absorbing silence
    words = [
        Word(text="one.", start=0.0, end=0.5),
        Word(text='"Suggest"', start=0.5, end=3.5),
    ]
    fixed = _recover_silences(words)
    assert fixed[0] == words[0]
    # The stretched word should now have a much shorter duration
    assert fixed[1].end == 3.5
    assert fixed[1].start > 0.5
    # The recovered gap should be > 1.5s
    assert fixed[1].start - fixed[0].end > 1.5


def test_recover_silences_leaves_normal_words():
    words = [
        Word(text="hello", start=0.0, end=0.4),
        Word(text="world", start=0.5, end=0.9),
    ]
    fixed = _recover_silences(words)
    assert fixed == words


def test_recover_silences_does_not_overlap_previous_word():
    # Previous word ends at 5.0, stretched word at 5.0-9.0
    # Recovered start must not go below 5.0
    words = [
        Word(text="end.", start=4.5, end=5.0),
        Word(text="next", start=5.0, end=9.0),
    ]
    fixed = _recover_silences(words)
    assert fixed[1].start >= 5.0


def test_estimate_speech_duration_short_word():
    assert _estimate_speech_duration("the") < 0.5


def test_estimate_speech_duration_long_word():
    assert _estimate_speech_duration("infinitive") > _estimate_speech_duration("the")


def test_estimate_speech_duration_punctuation_only():
    # Should still return a sensible minimum
    assert _estimate_speech_duration("...") >= 0.20


def _write_srt(content: str, encoding: str = "utf-8") -> str:
    """Write content to a temp .srt file and return the path."""
    f = tempfile.NamedTemporaryFile(
        mode="wb", suffix=".srt", delete=False
    )
    f.write(content.encode(encoding))
    f.close()
    return f.name


def test_simple_valid_srt():
    content = (
        "1\n"
        "00:00:01,000 --> 00:00:03,000\n"
        "Hello world.\n"
        "\n"
        "2\n"
        "00:00:04,000 --> 00:00:06,000\n"
        "Second subtitle.\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 2
    assert entries[0].text == "Hello world."
    assert entries[0].start == 1.0
    assert entries[0].end == 3.0
    assert entries[1].text == "Second subtitle."
    Path(path).unlink()


def test_srt_with_comma_decimal_separator():
    content = (
        "1\n"
        "00:00:01,500 --> 00:00:03,750\n"
        "Comma format.\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 1
    assert entries[0].start == 1.5
    assert entries[0].end == 3.75
    Path(path).unlink()


def test_srt_with_period_decimal_separator():
    content = (
        "1\n"
        "00:00:01.500 --> 00:00:03.750\n"
        "Period format.\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 1
    assert entries[0].start == 1.5
    assert entries[0].end == 3.75
    Path(path).unlink()


def test_srt_with_multiline_subtitle_text():
    content = (
        "1\n"
        "00:00:01,000 --> 00:00:04,000\n"
        "First line\n"
        "Second line\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 1
    assert "First line" in entries[0].text
    assert "Second line" in entries[0].text
    Path(path).unlink()


def test_empty_srt_file():
    path = _write_srt("")
    entries = parse_srt(path)
    assert entries == []
    Path(path).unlink()


def test_srt_with_extra_blank_lines():
    content = (
        "\n\n"
        "1\n"
        "00:00:01,000 --> 00:00:03,000\n"
        "Hello.\n"
        "\n\n\n"
        "2\n"
        "00:00:04,000 --> 00:00:06,000\n"
        "World.\n"
        "\n\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 2
    Path(path).unlink()


def test_srt_with_bom():
    content = "\ufeff1\n00:00:01,000 --> 00:00:03,000\nWith BOM.\n"
    f = tempfile.NamedTemporaryFile(
        mode="wb", suffix=".srt", delete=False
    )
    f.write(content.encode("utf-8-sig"))
    f.close()
    entries = parse_srt(f.name)
    assert len(entries) == 1
    assert entries[0].text == "With BOM."
    Path(f.name).unlink()


def test_malformed_timecodes_skipped():
    content = (
        "1\n"
        "INVALID TIMECODE\n"
        "Should be skipped.\n"
        "\n"
        "2\n"
        "00:00:04,000 --> 00:00:06,000\n"
        "Valid entry.\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 1
    assert entries[0].text == "Valid entry."
    Path(path).unlink()


def test_single_entry_srt():
    content = (
        "1\n"
        "00:01:00,000 --> 00:01:05,500\n"
        "Only one entry.\n"
    )
    path = _write_srt(content)
    entries = parse_srt(path)
    assert len(entries) == 1
    assert entries[0].start == 60.0
    assert entries[0].end == 65.5
    assert entries[0].text == "Only one entry."
    Path(path).unlink()
