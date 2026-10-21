# MemeGenerator

Generate a themed series of contextual images followed by reaction-video clips.

## Features (six stacked PRs)

1. Python 3.13 domain and strict quality gates.
2. Curated JSON catalog of local video clips and FFprobe validation.
3. LLM-generated, catalog-grounded scene scenarios.
4. Wikimedia Commons image search or local numbered images.
5. FFmpeg assembly.
6. Complete CLI and integrated tests.

## Image discovery

Default provider queries Wikimedia Commons' file search API and stores the
selected item's source URL and license attribution for each scene.
It filters media type, dimensions and download host, and prefers files whose
titles share keywords with the visual description. Commons search is not a
semantic image recognizer: visually irrelevant results can still occur.
For precise memes use local context images named `1.jpg`, `2.png`, etc.

Commons content must still be used according to each file's license.
No scraping of Google Images or automatic downloading of celebrity videos.

## Strict development checks

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest
```

No WPS rule exclusions.
