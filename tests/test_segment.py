from subcap.types import Word
from subcap.segment import segment_words, _wrap_lines, _line_count, _is_sentence_end
from subcap.types import SubtitleEntry


def _words(items):
    return [Word(t, s, e) for t, s, e in items]


# --- Basic segmentation ---

def test_single_sentence_fits_one_subtitle():
    words = _words([("Hello", 0.0, 0.5), ("world.", 0.6, 1.0)])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 1
    assert subs[0].text == "Hello world."


def test_long_silence_forces_break():
    # Two words with a 3-second gap between them — different "Question Time"
    # style breaks shouldn't be spanned by a single subtitle.
    words = _words([
        ("Ready", 0.0, 0.4),
        ("for", 0.5, 0.7),
        ("question", 0.8, 1.3),
        ("one", 1.4, 1.7),
        ("Number", 5.0, 5.4),  # 3.3s gap of silence
        ("two", 5.5, 5.8),
    ])
    subs = segment_words(words, max_chars=80, max_lines=2)
    assert len(subs) == 2
    assert subs[0].end == 1.7
    assert subs[1].start == 5.0
    # Subtitle 1 must end before silence starts
    assert subs[0].end < subs[1].start


def test_short_gap_does_not_force_break():
    # 0.5s gap — normal speech pause, should stay in one subtitle
    words = _words([
        ("Hello", 0.0, 0.4),
        ("there", 0.9, 1.2),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 1


def test_sentence_boundary_splits():
    words = _words([
        ("First", 0.0, 0.3), ("sentence.", 0.4, 0.8),
        ("Second", 1.2, 1.5), ("sentence.", 1.6, 2.0),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 2
    assert subs[0].text == "First sentence."
    assert subs[1].text == "Second sentence."


def test_long_line_wraps():
    words = _words([
        ("This", 0.0, 0.2), ("is", 0.3, 0.4), ("a", 0.5, 0.5),
        ("somewhat", 0.6, 0.8), ("longer", 0.9, 1.1),
        ("sentence", 1.2, 1.4), ("here.", 1.5, 1.8),
    ])
    subs = segment_words(words, max_chars=20, max_lines=2)
    for sub in subs:
        lines = sub.text.split("\\N")
        assert len(lines) <= 2


def test_max_lines_1():
    words = _words([
        ("Short", 0.0, 0.3), ("line.", 0.4, 0.7),
        ("Another", 1.0, 1.3), ("line.", 1.4, 1.7),
    ])
    subs = segment_words(words, max_chars=40, max_lines=1)
    for sub in subs:
        assert "\\N" not in sub.text


def test_empty_input():
    assert segment_words([], max_chars=40, max_lines=2) == []


def test_timing_uses_word_timestamps():
    words = _words([("Hello", 1.5, 2.0), ("world.", 2.5, 3.0)])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert subs[0].start == 1.5
    assert subs[0].end == 3.0


# --- New: edge cases ---

def test_single_word_input():
    words = _words([("Hello.", 0.0, 0.5)])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 1
    assert subs[0].text == "Hello."
    assert subs[0].start == 0.0
    assert subs[0].end == 0.5


def test_question_mark_ends_sentence():
    words = _words([
        ("Is", 0.0, 0.2), ("this", 0.3, 0.5), ("real?", 0.6, 1.0),
        ("Yes", 1.2, 1.5), ("indeed.", 1.6, 2.0),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 2
    assert subs[0].text == "Is this real?"
    assert subs[1].text == "Yes indeed."


def test_exclamation_mark_ends_sentence():
    words = _words([
        ("Wow!", 0.0, 0.5),
        ("That", 0.8, 1.0), ("was", 1.1, 1.3), ("great.", 1.4, 1.8),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 2
    assert subs[0].text == "Wow!"
    assert subs[1].text == "That was great."


def test_very_long_text_forces_multiple_subtitles():
    # 20 words without sentence-ending punctuation, narrow max_chars
    items = [(f"word{i}", i * 0.3, i * 0.3 + 0.25) for i in range(20)]
    words = _words(items)
    subs = segment_words(words, max_chars=15, max_lines=2)
    assert len(subs) > 1
    for sub in subs:
        lines = sub.text.split("\\N")
        assert len(lines) <= 2


def test_subtitle_with_exactly_max_chars_boundary():
    # "aaaa bbbb" is exactly 9 chars; max_chars=9 should fit on one line
    words = _words([("aaaa", 0.0, 0.5), ("bbbb.", 0.6, 1.0)])
    subs = segment_words(words, max_chars=9, max_lines=2)
    assert len(subs) == 1
    # Should not need wrapping since "aaaa bbbb." is 10 chars but
    # _wrap_lines checks > max_chars, so exactly at boundary stays on one line


def test_words_with_very_long_gaps():
    words = _words([
        ("First", 0.0, 0.5),
        ("second", 10.0, 10.5),
        ("third.", 20.0, 20.5),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    # All end up in one subtitle because no sentence boundary until "third."
    # but the 8-second duration cap should split them
    assert len(subs) >= 2


def test_duration_capping_at_eight_seconds():
    # Words spanning more than 8 seconds without sentence boundary
    words = _words([
        ("one", 0.0, 0.5),
        ("two", 1.0, 1.5),
        ("three", 2.0, 2.5),
        ("four", 3.0, 3.5),
        ("five", 4.0, 4.5),
        ("six", 5.0, 5.5),
        ("seven", 6.0, 6.5),
        ("eight", 7.0, 7.5),
        ("nine", 8.0, 8.5),  # adding this would exceed 8s from word "one"
        ("ten", 9.0, 9.5),
    ])
    subs = segment_words(words, max_chars=80, max_lines=2)
    # At least one split should occur due to 8-second cap
    assert len(subs) >= 2
    for sub in subs:
        assert sub.end - sub.start <= 8.0 + 0.01  # small tolerance


def test_max_lines_3():
    words = _words([
        ("This", 0.0, 0.2), ("is", 0.3, 0.4), ("a", 0.5, 0.5),
        ("longer", 0.6, 0.8), ("text", 0.9, 1.0),
        ("that", 1.1, 1.2), ("needs", 1.3, 1.5),
        ("wrapping", 1.6, 1.9), ("here.", 2.0, 2.3),
    ])
    subs = segment_words(words, max_chars=15, max_lines=3)
    for sub in subs:
        lines = sub.text.split("\\N")
        assert len(lines) <= 3


def test_unicode_text():
    words = _words([
        ("Caf\u00e9", 0.0, 0.5), ("na\u00efve", 0.6, 1.0), ("r\u00e9sum\u00e9.", 1.1, 1.5),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 1
    assert "Caf\u00e9" in subs[0].text
    assert "na\u00efve" in subs[0].text


def test_text_with_em_dash():
    words = _words([
        ("Well\u2014", 0.0, 0.5), ("that", 0.6, 0.9), ("works.", 1.0, 1.4),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) == 1
    assert "\u2014" in subs[0].text


def test_start_end_times_monotonically_increasing():
    words = _words([
        ("First", 0.0, 0.3), ("sentence.", 0.4, 0.8),
        ("Second", 1.0, 1.3), ("sentence.", 1.4, 1.8),
        ("Third", 2.0, 2.3), ("sentence.", 2.4, 2.8),
    ])
    subs = segment_words(words, max_chars=40, max_lines=2)
    for i in range(len(subs)):
        assert subs[i].start < subs[i].end
        if i > 0:
            assert subs[i].start >= subs[i - 1].end


def test_large_input_produces_reasonable_count():
    # 60 words, each ~0.3s apart, no sentence enders except last
    items = [(f"word{i}", i * 0.4, i * 0.4 + 0.3) for i in range(59)]
    items.append(("done.", 59 * 0.4, 59 * 0.4 + 0.3))
    words = _words(items)
    subs = segment_words(words, max_chars=40, max_lines=2)
    assert len(subs) >= 3
    assert len(subs) <= 60  # at most one per word


# --- Internal helpers ---

def test_is_sentence_end_period():
    assert _is_sentence_end("hello.") is True


def test_is_sentence_end_question():
    assert _is_sentence_end("what?") is True


def test_is_sentence_end_exclamation():
    assert _is_sentence_end("wow!") is True


def test_is_sentence_end_no_punctuation():
    assert _is_sentence_end("hello") is False


def test_is_sentence_end_empty_string():
    assert _is_sentence_end("") is False


def test_wrap_lines_fits_single_line():
    result = _wrap_lines(["Hello", "world"], 20)
    assert result == "Hello world"


def test_wrap_lines_wraps_at_boundary():
    result = _wrap_lines(["Hello", "beautiful", "world"], 10)
    assert "\\N" in result
    lines = result.split("\\N")
    for line in lines:
        assert len(line) <= 10 or len(line.split()) == 1


def test_line_count_empty():
    assert _line_count([], 40) == 0


def test_line_count_single_word():
    assert _line_count(["hello"], 40) == 1


def test_line_count_wraps():
    count = _line_count(["This", "is", "a", "long", "sentence"], 10)
    assert count >= 2
