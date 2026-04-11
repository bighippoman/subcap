import pytest

from subcap.styles import generate_ass, StyleConfig, style_for_video, _fmt_time, PRESET_NAMES
from subcap.types import SubtitleEntry


# --- generate_ass structure ---

def test_generate_ass_structure():
    subs = [
        SubtitleEntry(start=1.0, end=3.0, text="Hello world."),
        SubtitleEntry(start=4.0, end=6.0, text="Second line."),
    ]
    config = style_for_video("modern", 1920, 1080)
    ass = generate_ass(subs, config)
    assert "[Script Info]" in ass
    assert "[V4+ Styles]" in ass
    assert "[Events]" in ass
    assert "Hello world." in ass
    assert "0:00:01.00" in ass


def test_generate_ass_empty_subtitle_list():
    config = style_for_video("modern", 1920, 1080)
    ass = generate_ass([], config)
    assert "[Script Info]" in ass
    assert "[V4+ Styles]" in ass
    assert "[Events]" in ass
    assert "Dialogue:" not in ass


def test_generate_ass_single_subtitle():
    subs = [SubtitleEntry(start=0.0, end=2.0, text="Only one.")]
    config = style_for_video("modern", 1920, 1080)
    ass = generate_ass(subs, config)
    assert ass.count("Dialogue:") == 1
    assert "Only one." in ass


# --- style_for_video ---

def test_style_for_landscape():
    config = style_for_video("modern", 1920, 1080)
    assert config.font_size >= 50


def test_style_for_portrait():
    config = style_for_video("modern", 1080, 1920)
    assert config.font_size <= 46


def test_all_presets_exist():
    for preset in ("modern", "outline", "minimal", "bold"):
        config = style_for_video(preset, 1920, 1080)
        assert config.font_name


def test_invalid_preset():
    with pytest.raises(ValueError):
        style_for_video("nonexistent", 1920, 1080)


def test_all_four_presets_produce_different_ass():
    subs = [SubtitleEntry(start=0.0, end=1.0, text="Test.")]
    outputs = set()
    for preset in PRESET_NAMES:
        config = style_for_video(preset, 1920, 1080)
        ass = generate_ass(subs, config)
        outputs.add(ass)
    assert len(outputs) == 4


def test_position_bottom_alignment():
    config = style_for_video("modern", 1920, 1080, position="bottom")
    assert config.alignment == 2


def test_position_top_alignment():
    config = style_for_video("modern", 1920, 1080, position="top")
    assert config.alignment == 8


def test_position_center_alignment():
    config = style_for_video("modern", 1920, 1080, position="center")
    assert config.alignment == 5


def test_position_changes_ass_alignment_value():
    subs = [SubtitleEntry(start=0.0, end=1.0, text="Test.")]
    config_bottom = style_for_video("modern", 1920, 1080, position="bottom")
    config_top = style_for_video("modern", 1920, 1080, position="top")
    ass_bottom = generate_ass(subs, config_bottom)
    ass_top = generate_ass(subs, config_top)
    assert ass_bottom != ass_top


def test_line_spacing_reflected_in_config():
    config = style_for_video("modern", 1920, 1080, line_spacing=5.0)
    assert config.spacing == 5.0


def test_line_spacing_default_is_zero():
    config = style_for_video("modern", 1920, 1080)
    assert config.spacing == 0.0


def test_line_spacing_in_ass_output():
    subs = [SubtitleEntry(start=0.0, end=1.0, text="Test.")]
    config_spaced = style_for_video("modern", 1920, 1080, line_spacing=10.0)
    config_default = style_for_video("modern", 1920, 1080)
    ass_spaced = generate_ass(subs, config_spaced)
    ass_default = generate_ass(subs, config_default)
    assert ass_spaced != ass_default


def test_portrait_vs_landscape_different_font_sizes():
    landscape = style_for_video("modern", 1920, 1080)
    portrait = style_for_video("modern", 1080, 1920)
    assert landscape.font_size != portrait.font_size


def test_portrait_vs_landscape_different_margins():
    landscape = style_for_video("modern", 1920, 1080)
    portrait = style_for_video("modern", 1080, 1920)
    assert landscape.margin_l != portrait.margin_l


# --- _fmt_time ---

def test_ass_time_format():
    subs = [SubtitleEntry(start=65.5, end=68.25, text="Test.")]
    config = style_for_video("modern", 1920, 1080)
    ass = generate_ass(subs, config)
    assert "0:01:05.50" in ass
    assert "0:01:08.25" in ass


def test_fmt_time_zero_seconds():
    assert _fmt_time(0.0) == "0:00:00.00"


def test_fmt_time_exactly_one_hour():
    assert _fmt_time(3600.0) == "1:00:00.00"


def test_fmt_time_sub_centisecond_rounds():
    # 1.005 seconds -> 1.01 (rounds to nearest centisecond)
    result = _fmt_time(1.005)
    assert result == "0:00:01.01" or result == "0:00:01.00"  # rounding


def test_fmt_time_large_value():
    result = _fmt_time(7261.99)
    assert result.startswith("2:01:01")
