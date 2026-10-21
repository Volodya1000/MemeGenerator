# MemeGenerator

Generate a topical video where every contextual image is followed by a reaction
from a **curated library of real video clips**. No voice cloning or deepfakes.

## Roadmap

1. Project structure, validated domain contracts, strict CI.
2. Curated and validated meme catalog.
3. LLM planner using OpenAI-compatible APIs and strict JSON output.
4. Relevant image discovery from licensed sources and local images.
5. FFmpeg normalization and montage.
6. Integrated CLI, reproducible demos, integration tests.

Python **3.13**, FFmpeg and ffprobe are required. Keep copyrighted source clips
outside Git. Importing clips is an explicit operation, never part of CI or
normal application startup. See [curated asset import](docs/meme-assets.md).

```bash
uv sync --extra dev
uv run meme-assets --download
```

The reviewed source manifest includes direct MP4 URLs for seven short reactions.
`--download` explicitly opts into downloading missing originals from Cutzo's
public CDN; without it, only local clips are used. Media is never committed to
Git or downloaded as part of the standard CI. Run the real-media verification
workflow manually when needed.

## Quality

Wemake Python Styleguide 1.8.1 with **every WPS rule enabled** and **no
per-file or inline WPS ignores**, plus Ruff, strict mypy, and pytest.
The small Ruff compatibility exclusions in pyproject.toml prevent mutually
exclusive docstring/formatter rules; they do not disable WPS checks.

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest -m 'not integration'
uv run pytest -m integration
```
