from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_QUALITY = {
    "standard": {
        "codec": ["-c:v", "libx264", "-crf", "18", "-preset", "medium"],
        "ext": ".mp4",
    },
    "high": {
        "codec": ["-c:v", "libx265", "-crf", "22", "-preset", "medium"],
        "ext": ".mp4",
    },
    "studio": {
        "codec": ["-c:v", "prores_ks", "-profile:v", "2", "-pix_fmt", "yuv422p10le"],
        "ext": ".mov",
    },
}

QUALITY_NAMES = tuple(_QUALITY.keys())


def default_output_path(input_path: str | Path, quality: str) -> Path:
    p = Path(input_path)
    ext = _QUALITY[quality]["ext"]
    return p.with_stem(p.stem + "_captioned").with_suffix(ext)


def encode(
    video_path: str | Path,
    ass_content: str,
    output_path: str | Path,
    quality: str = "standard",
) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ass", delete=False, encoding="utf-8"
    ) as f:
        f.write(ass_content)
        ass_path = f.name

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"ass={ass_path}",
        *_QUALITY[quality]["codec"],
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-y",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            stderr = result.stderr
            if "ass" in stderr.lower() and "unknown" in stderr.lower():
                print(
                    "Error: ffmpeg missing libass support.\n"
                    "Install a full build with subtitle rendering.",
                    file=sys.stderr,
                )
            else:
                print(f"ffmpeg error:\n{stderr[-500:]}", file=sys.stderr)
            raise SystemExit(1)
    finally:
        Path(ass_path).unlink(missing_ok=True)
