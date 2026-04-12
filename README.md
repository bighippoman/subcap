# subcap

A one-command captioning pipeline built around [WhisperX](https://github.com/m-bain/whisperX)'s forced alignment. Give it a video and a transcript — it handles audio extraction, alignment, subtitle segmentation, styling, and burn-in encoding.

## Why this exists

WhisperX solves the hard problem: using wav2vec2 to map each word of a known transcript to its exact position in audio. But WhisperX outputs raw word timestamps — turning those into readable, styled, burned-in captions is still a non-trivial amount of glue code per video.

subcap is that glue code, packaged as a CLI:

- **Subtitle segmentation** — groups aligned words into readable chunks with sentence-boundary breaks, line wrapping, duration caps, and proper gaps between cues
- **Styled ASS generation** — four presets (modern, outline, minimal, bold), auto-adapted for landscape vs portrait video
- **ffmpeg burn-in** — re-encodes to H.264, H.265, or ProRes with a single `--quality` flag
- **SRT bypass** — if you already have timed subtitles, it skips alignment and goes straight to styling + burn-in

Without subcap, getting from *video + transcript* to *video with burned-in captions* requires chaining WhisperX, writing your own segmentation logic, hand-crafting ASS files, and orchestrating ffmpeg. subcap is `subcap video.mov transcript.txt`.

## Install

```
pip install subcap
```

Requires Python 3.10–3.12 and [ffmpeg](https://ffmpeg.org/) with libass support.

On first run, subcap downloads the wav2vec2 alignment model (~360 MB).

## Usage

```bash
# Align a transcript and burn captions in
subcap video.mov transcript.txt -o output.mp4

# Use an existing SRT file (skips alignment)
subcap video.mov subtitles.srt -o output.mp4

# Choose a style
subcap video.mov transcript.txt --style outline

# ProRes output for editing
subcap video.mov transcript.txt --quality studio -o output.mov

# Portrait/vertical video (auto-detected)
subcap shorts.mp4 transcript.txt -o shorts_captioned.mp4
```

## Options

```
subcap <video> <transcript> [options]

  -o, --output          Output path (default: <input>_captioned.mp4)
  --style               modern | outline | minimal | bold (default: modern)
  --quality             standard | high | studio (default: standard)
  --max-lines           Max lines per subtitle (default: 2)
  --max-chars           Max characters per line (default: auto)
  --line-spacing        Gap between lines in px (default: auto)
  --position            bottom | center | top (default: bottom)
```

### Styles

| Preset | Look |
|--------|------|
| `modern` | White bold text, semi-transparent dark box |
| `outline` | White text with black outline |
| `minimal` | Lighter weight, subtle shadow |
| `bold` | Large text, opaque dark box |

### Quality

| Preset | Codec | Use case |
|--------|-------|----------|
| `standard` | H.264 | Sharing, uploading |
| `high` | H.265 | Smaller files |
| `studio` | ProRes 422 | Editing, broadcast |

## Pipeline

1. **Extract audio** — mono 16 kHz WAV via ffmpeg
2. **Force-align** (WhisperX / wav2vec2) — map each word of the transcript to its exact position in the audio
3. **Segment** (subcap) — group words into readable subtitle cues, break at sentence boundaries, wrap long lines, enforce min/max display duration, insert gaps
4. **Style** (subcap) — generate ASS with the selected preset, adapted to aspect ratio
5. **Burn in** (ffmpeg) — re-encode with hardcoded subtitles

Steps 1, 2, and 5 are wrappers around existing tools. Steps 3 and 4 are what subcap adds. Because the transcript text is fixed and only timing is being solved, alignment stays precise even for fast speech, accents, or noisy audio — conditions that break speech-to-text approaches.

### Transcript notes

Your transcript must match what's actually said in the audio. Small edits are tolerated, but missing or extra sentences will cause alignment failures. If the speaker ad-libs or skips text, update the transcript to match the final delivery.

## Acknowledgments

Built on:

- **[WhisperX](https://github.com/m-bain/whisperX)** — Phoneme-level forced alignment using wav2vec2
- **[wav2vec2](https://github.com/facebookresearch/fairseq/tree/main/examples/wav2vec)** — Self-supervised speech model used as the acoustic backbone for alignment
- **[ffmpeg](https://ffmpeg.org/)** — Video encoding and subtitle rendering via libass

## License

MIT
