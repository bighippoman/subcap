import subprocess
import sys

import pytest

from subcap.cli import main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "subcap" in captured.out
    assert "0." in captured.out  # version starts with 0.x


def test_help_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "subcap" in captured.out.lower()


def test_missing_video_file(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_video.mp4", "transcript.txt"])
    assert exc_info.value.code != 0


def test_missing_transcript_file(tmp_path, capsys):
    # Create a real video file so the first check passes
    video = tmp_path / "video.mp4"
    video.write_bytes(b"\x00")
    with pytest.raises(SystemExit) as exc_info:
        main([str(video), "nonexistent_transcript.txt"])
    assert exc_info.value.code != 0


def test_invalid_style_name(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["video.mp4", "transcript.txt", "--style", "fakestyle"])
    assert exc_info.value.code != 0


def test_invalid_quality_name(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["video.mp4", "transcript.txt", "--quality", "fakequality"])
    assert exc_info.value.code != 0
