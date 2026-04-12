# subcap

Burn precisely-timed captions into video. Give it a video and a transcript — it handles alignment, styling, and encoding.

Unlike speech-to-text tools that guess both *what* is said and *when*, subcap uses **forced alignment**: you provide the transcript, and wav2vec2 maps each word to its exact position in the audio waveform. The result is phoneme-level timing accuracy — no drift, no guessing, no cascading errors.

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

## How it works

1. Extracts audio from the video
2. Runs phoneme-level forced alignment via [WhisperX](https://github.com/m-bain/whisperX) (wav2vec2) to map each word of your transcript to its exact position in the audio
3. Segments words into readable subtitle chunks, breaking at sentence boundaries
4. Generates styled ASS subtitles adapted to the video's aspect ratio
5. Burns captions into the video via ffmpeg

Because the text is fixed and only the timing is being solved, alignment is precise even for fast speech, accents, or overlapping audio — conditions that typically break speech-to-text.

### Transcript notes

Your transcript must match what's actually said in the audio. Small edits are tolerated, but missing or extra sentences will cause alignment failures. If the speaker ad-libs or skips text, update the transcript to match the final delivery.

## Acknowledgments

Built on:

- **[WhisperX](https://github.com/m-bain/whisperX)** — Phoneme-level forced alignment using wav2vec2
- **[wav2vec2](https://github.com/facebookresearch/fairseq/tree/main/examples/wav2vec)** — Self-supervised speech model used as the acoustic backbone for alignment
- **[ffmpeg](https://ffmpeg.org/)** — Video encoding and subtitle rendering via libass

## License

MIT
