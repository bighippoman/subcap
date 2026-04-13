from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from subcap.types import SubtitleEntry, Word


def _estimate_speech_duration(text: str) -> float:
    """Plausible upper bound on how long a single word takes to say."""
    chars = sum(1 for c in text if c.isalpha())
    return max(0.20, chars * 0.08 + 0.12)


def _recover_silences(words: list[Word]) -> list[Word]:
    """Clip word starts that wav2vec2 stretched over preceding silence.

    wav2vec2's forced alignment hides silences by extending the duration of
    the next spoken word — a 0.5s word can be marked as 3s long if there's
    a 2.5s pause before it. This walks each word, and if its duration is
    much longer than character-count would predict, clips its start time
    so the silence becomes a real gap that segmentation can act on.
    """
    fixed: list[Word] = []
    for i, w in enumerate(words):
        actual = w.end - w.start
        plausible = _estimate_speech_duration(w.text)
        if actual > plausible * 1.6 and actual > 0.8:
            new_start = w.end - plausible
            prev_end = fixed[-1].end if fixed else 0.0
            new_start = max(new_start, prev_end)
            fixed.append(Word(text=w.text, start=new_start, end=w.end))
        else:
            fixed.append(w)
    return fixed


def align_transcript(
    video_path: str | Path,
    transcript: str,
    language: str = "en",
) -> list[Word]:
    """Force-align a known transcript to a video's audio track.

    Uses wav2vec2 via WhisperX for phoneme-level alignment. The transcript
    text is treated as ground truth — each word is mapped to its exact
    position in the audio.
    """
    import whisperx  # lazy import — keeps module load fast

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-ac", "1",
                "-ar", "16000",
                "-vn",
                wav_path,
            ],
            capture_output=True,
            check=True,
        )

        audio = whisperx.load_audio(wav_path)
        duration = len(audio) / 16000

        normalized = re.sub(r"\s+", " ", transcript).strip()
        segments = [{"text": normalized, "start": 0.0, "end": duration}]

        model, metadata = whisperx.load_align_model(
            language_code=language, device="cpu"
        )
        result = whisperx.align(
            segments, model, metadata, audio, device="cpu",
            return_char_alignments=False,
        )

        words: list[Word] = []
        for segment in result["segments"]:
            for w in segment.get("words", []):
                if "start" in w and "end" in w:
                    words.append(Word(
                        text=w["word"],
                        start=float(w["start"]),
                        end=float(w["end"]),
                    ))
        return _recover_silences(words)
    finally:
        Path(wav_path).unlink(missing_ok=True)


_TIMECODE_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
    r"\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


def _tc_to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(path: str | Path) -> list[SubtitleEntry]:
    text = Path(path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n{2,}", text.strip())

    entries: list[SubtitleEntry] = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue

        # Find the timecode line (skip the index line)
        tc_line_idx = None
        for i, line in enumerate(lines):
            if _TIMECODE_RE.search(line):
                tc_line_idx = i
                break
        if tc_line_idx is None:
            continue

        m = _TIMECODE_RE.search(lines[tc_line_idx])
        start = _tc_to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
        end = _tc_to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
        body = " ".join(lines[tc_line_idx + 1 :]).strip()

        if body:
            entries.append(SubtitleEntry(start=start, end=end, text=body))

    return entries
