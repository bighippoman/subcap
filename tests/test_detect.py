from pathlib import Path

import pytest

from subcap.detect import is_srt, VideoInfo, parse_video_info_output


# --- is_srt ---

def test_is_srt_with_srt_extension():
    assert is_srt("subtitles.srt") is True


def test_is_srt_with_txt_extension():
    assert is_srt("transcript.txt") is False


def test_is_srt_with_no_extension():
    assert is_srt("transcript") is False


def test_is_srt_uppercase_extension():
    assert is_srt("subtitles.SRT") is True


def test_is_srt_mixed_case_extension():
    assert is_srt("subtitles.Srt") is True


def test_is_srt_with_path_object():
    assert is_srt(Path("dir/subtitles.srt")) is True


def test_is_srt_path_object_non_srt():
    assert is_srt(Path("dir/subtitles.vtt")) is False


# --- parse_video_info_output ---

def test_parse_video_info_landscape():
    probe = {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080},
            {"codec_type": "audio"},
        ],
        "format": {"duration": "120.5"},
    }
    info = parse_video_info_output(probe)
    assert info.width == 1920
    assert info.height == 1080
    assert info.duration == 120.5
    assert info.is_portrait is False


def test_parse_video_info_portrait():
    probe = {
        "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920},
        ],
        "format": {"duration": "60.0"},
    }
    info = parse_video_info_output(probe)
    assert info.is_portrait is True


def test_parse_video_info_no_video_stream():
    probe = {
        "streams": [{"codec_type": "audio"}],
        "format": {"duration": "60.0"},
    }
    with pytest.raises(ValueError, match="video stream"):
        parse_video_info_output(probe)


def test_parse_video_info_square_aspect_ratio():
    probe = {
        "streams": [{"codec_type": "video", "width": 1080, "height": 1080}],
        "format": {"duration": "30.0"},
    }
    info = parse_video_info_output(probe)
    assert info.width == 1080
    assert info.height == 1080
    assert info.is_portrait is False  # width >= height


def test_parse_video_info_missing_duration_key():
    probe = {
        "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
        "format": {},
    }
    with pytest.raises(KeyError):
        parse_video_info_output(probe)


def test_parse_video_info_multiple_video_streams_uses_first():
    probe = {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080},
            {"codec_type": "video", "width": 640, "height": 480},
            {"codec_type": "audio"},
        ],
        "format": {"duration": "90.0"},
    }
    info = parse_video_info_output(probe)
    assert info.width == 1920
    assert info.height == 1080


def test_parse_video_info_empty_streams():
    probe = {
        "streams": [],
        "format": {"duration": "60.0"},
    }
    with pytest.raises(ValueError, match="video stream"):
        parse_video_info_output(probe)
