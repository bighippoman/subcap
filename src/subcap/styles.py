from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from subcap.types import SubtitleEntry

PRESET_NAMES = ("modern", "outline", "minimal", "bold")

_POSITION_MAP = {"bottom": 2, "center": 5, "top": 8}


@dataclass(frozen=True)
class StyleConfig:
    font_name: str
    font_size: int
    bold: bool
    primary_color: str
    outline_color: str
    back_color: str
    border_style: int
    outline: int
    shadow: int
    margin_l: int
    margin_r: int
    margin_v: int
    alignment: int
    spacing: float
    play_res_x: int
    play_res_y: int


def style_for_video(
    preset: str,
    width: int,
    height: int,
    line_spacing: float | None = None,
    position: str = "bottom",
) -> StyleConfig:
    if preset not in PRESET_NAMES:
        raise ValueError(f"Unknown preset {preset!r}. Valid: {PRESET_NAMES}")

    alignment = _POSITION_MAP.get(position, 2)
    landscape = width >= height

    font_size = 56 if landscape else 42
    margin_h = 100 if landscape else 40
    margin_v = 50 if landscape else 80

    spacing = line_spacing if line_spacing is not None else 0.0

    base = dict(
        font_name="Arial",
        font_size=font_size,
        bold=True,
        primary_color="&H00FFFFFF",
        outline_color="&H00000000",
        back_color="&H50000000",
        border_style=3,
        outline=14,
        shadow=0,
        margin_l=margin_h,
        margin_r=margin_h,
        margin_v=margin_v,
        alignment=alignment,
        spacing=spacing,
        play_res_x=width,
        play_res_y=height,
    )

    if preset == "modern":
        pass  # defaults above
    elif preset == "outline":
        base.update(back_color="&H00000000", border_style=1, outline=3)
    elif preset == "minimal":
        base.update(
            bold=False,
            back_color="&HA0000000",
            border_style=1,
            outline=1,
            shadow=2,
        )
    elif preset == "bold":
        base.update(back_color="&H00000000", border_style=3, outline=16)

    return StyleConfig(**base)


def _fmt_time(seconds: float) -> str:
    """Format seconds as ASS time H:MM:SS.CC (centiseconds)."""
    cs = round(seconds * 100)
    h = cs // 360000
    cs %= 360000
    m = cs // 6000
    cs %= 6000
    s = cs // 100
    cs %= 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_ass(subs: Sequence[SubtitleEntry], config: StyleConfig) -> str:
    bold_val = -1 if config.bold else 0

    style_line = (
        f"Style: Default,{config.font_name},{config.font_size},"
        f"{config.primary_color},{config.primary_color},"
        f"{config.outline_color},{config.back_color},"
        f"{bold_val},0,0,0,"
        f"100,100,{config.spacing},0,"
        f"{config.border_style},{config.outline},{config.shadow},"
        f"{config.alignment},"
        f"{config.margin_l},{config.margin_r},{config.margin_v},1"
    )

    dialogue_lines = [
        f"Dialogue: 0,{_fmt_time(s.start)},{_fmt_time(s.end)},Default,,0,0,0,,{s.text}"
        for s in subs
    ]

    sections = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        f"PlayResX: {config.play_res_x}",
        f"PlayResY: {config.play_res_y}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        style_line,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *dialogue_lines,
    ]

    return "\n".join(sections)
