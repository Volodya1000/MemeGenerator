# MemeGenerator

Automated contextual-image → curated reaction-video storytelling.

**Requirements:** Python 3.13, FFmpeg / FFprobe, legally obtained
reaction video files.

## Roadmap (stacked PRs)

1. Models and uncompromising CI.
2. JSON clip catalog and FFprobe validation.
3. OpenAI-compatible LLM planner and offline deterministic planner.
4. Image retrieval and local asset support.
5. FFmpeg video assembly.
6. Complete CLI + integration tests.

## LLM contract

The planner receives the theme and an explicit allowlist of identifiers and
spoken phrases. It returns JSON containing ordered scenes, specific image
search terms and *only known* `meme_id` values. The application validates
every identifier before accessing the media. The LLM never creates video
content or invents new phrases.

Compatible with OpenAI API and local OpenAI-compatible servers.
An offline demo planner is included for repeatable tests (not funny by
design; use an LLM for semantic planning).

## Local setup

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest
```

WPS v1.8.1: no rule or per-file WPS suppression.
