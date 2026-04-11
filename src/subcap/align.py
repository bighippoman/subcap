from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from subcap.types import SubtitleEntry, Word


def align_transcript(video_path: str | Path, transcript: str) -> list[Word]:
    import stable_whisper  # lazy import — keeps module load fast

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

        model = stable_whisper.load_model("medium")
        result = model.align(wav_path, transcript, language="en")

        words: list[Word] = []
        for segment in result.segments:
            for w in segment.words:
                words.append(Word(text=w.word, start=w.start, end=w.end))
        return words
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
