from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    duration: float

    @property
    def is_portrait(self) -> bool:
        return self.height > self.width


def is_srt(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".srt"


def parse_video_info_output(probe: dict) -> VideoInfo:
    video = next(
        (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    if video is None:
        raise ValueError("No video stream found in probe output")
    return VideoInfo(
        width=int(video["width"]),
        height=int(video["height"]),
        duration=float(probe["format"]["duration"]),
    )


def probe_video(path: str | Path) -> VideoInfo:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_video_info_output(json.loads(result.stdout))


def check_ffmpeg() -> None:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit(
            "ffmpeg not found. Install it with libass support:\n"
            "  macOS:  brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Arch:   sudo pacman -S ffmpeg"
        )

    if "libass" not in result.stdout + result.stderr:
        sys.exit(
            "ffmpeg is installed but was not compiled with libass support.\n"
            "  macOS:  brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Arch:   sudo pacman -S ffmpeg"
        )
