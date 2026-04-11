from pathlib import Path

from subcap.encode import default_output_path, QUALITY_NAMES


# --- default_output_path ---

def test_default_output_path_standard():
    result = default_output_path("video.mp4", "standard")
    assert result == Path("video_captioned.mp4")


def test_default_output_path_high():
    result = default_output_path("video.mp4", "high")
    assert result == Path("video_captioned.mp4")


def test_default_output_path_studio():
    result = default_output_path("video.mp4", "studio")
    assert result == Path("video_captioned.mov")


def test_default_output_path_preserves_directory():
    result = default_output_path("/tmp/projects/video.mp4", "standard")
    assert result == Path("/tmp/projects/video_captioned.mp4")


def test_default_output_path_with_path_object():
    result = default_output_path(Path("video.mov"), "standard")
    assert result == Path("video_captioned.mp4")


# --- QUALITY_NAMES ---

def test_quality_names_contains_standard():
    assert "standard" in QUALITY_NAMES


def test_quality_names_contains_high():
    assert "high" in QUALITY_NAMES


def test_quality_names_contains_studio():
    assert "studio" in QUALITY_NAMES


def test_quality_names_has_three_entries():
    assert len(QUALITY_NAMES) == 3
