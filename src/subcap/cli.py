from __future__ import annotations

import argparse
import sys
from pathlib import Path

from subcap import __version__
from subcap.detect import check_ffmpeg, is_srt, probe_video
from subcap.encode import QUALITY_NAMES, default_output_path, encode
from subcap.segment import segment_words
from subcap.types import SubtitleEntry
from subcap.styles import PRESET_NAMES, generate_ass, style_for_video


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="subcap",
        description="Burn captions into video using forced alignment.",
    )
    parser.add_argument("video", help="Input video file")
    parser.add_argument("transcript", help="Transcript file (.srt or plain text)")
    parser.add_argument("-o", "--output", help="Output file path (default: auto)")
    parser.add_argument(
        "--style",
        choices=PRESET_NAMES,
        default="modern",
        help="Caption style preset (default: modern)",
    )
    parser.add_argument(
        "--quality",
        choices=QUALITY_NAMES,
        default="standard",
        help="Encoding quality preset (default: standard)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=2,
        metavar="N",
        help="Maximum subtitle lines per card (default: 2)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=None,
        metavar="N",
        help="Maximum characters per line (default: auto)",
    )
    parser.add_argument(
        "--line-spacing",
        type=int,
        default=None,
        metavar="N",
        help="Extra line spacing in pixels (default: auto)",
    )
    parser.add_argument(
        "--position",
        choices=("bottom", "center", "top"),
        default="bottom",
        help="Vertical caption position (default: bottom)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args(argv)

    video_path = Path(args.video)
    transcript_path = Path(args.transcript)

    if not video_path.exists():
        parser.error(f"Video file not found: {video_path}")
    if not transcript_path.exists():
        parser.error(f"Transcript file not found: {transcript_path}")

    check_ffmpeg()

    print(f"Probing {video_path.name}...")
    info = probe_video(video_path)
    print(f"  {info.width}x{info.height}, {info.duration:.1f}s")

    max_chars = args.max_chars
    if max_chars is None:
        max_chars = 28 if info.is_portrait else 42

    if is_srt(transcript_path):
        from subcap.align import parse_srt

        subs = parse_srt(transcript_path)
        print(f"  {len(subs)} subtitles")
    else:
        from subcap.align import align_transcript

        transcript_text = transcript_path.read_text(encoding="utf-8")
        print("Aligning transcript to audio (this may take a minute)...")
        words = align_transcript(video_path, transcript_text)
        print(f"  Aligned {len(words)} words")
        subs = segment_words(words, max_chars=max_chars, max_lines=args.max_lines)
        print(f"  {len(subs)} subtitles")

    style = style_for_video(
        args.style,
        info.width,
        info.height,
        line_spacing=args.line_spacing,
        position=args.position,
    )
    ass_content = generate_ass(subs, style)

    output_path = Path(args.output) if args.output else default_output_path(video_path, args.quality)
    print(f"Encoding \u2192 {output_path.name}")
    encode(video_path, ass_content, output_path, quality=args.quality)

    print("Done.")


if __name__ == "__main__":
    main()
