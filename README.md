# MemeGenerator

Create a themed video where each contextual image is followed by a reaction
from a **curated library of existing video clips**. No voice cloning or
synthetic representation of Oleg Tinkov.

Python **3.13**, FFmpeg and FFprobe are required.

## Catalog

Copy `assets/memes.example.json` to `assets/memes.json`, place video clips
under `assets/memes/`, and replace the placeholder entry with your own
`meme_id`, exact spoken `phrase`, and relative `video_path`.

The catalog refuses duplicate identifiers, missing files, path traversal
and unsupported media extensions. FFprobe checks media streams and duration.
Provide only clips you have the right to use. No celebrity clips are bundled.

## Six PR roadmap

1. Typed foundation + strict CI.
2. Validated meme catalog + probing.
3. LLM planner using only known meme IDs.
4. Image discovery and local image support.
5. FFmpeg montage.
6. Integrated CLI, docs and full testing.

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest
```

Wemake 1.8.1: every WPS rule enabled, no WPS suppression.
