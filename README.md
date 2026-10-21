# MemeGenerator

Python 3.13 utility for themed reaction videos using a user-supplied catalog
of existing celebrity clips. It **does not synthesize voices or faces**.

## Implemented components

- Validated JSON reaction-video catalog and media probing.
- OpenAI-compatible LLM with strict catalog-grounded scene planning.
- Wikimedia Commons image finder or numbered user-provided images.
- FFmpeg still context images followed by recorded reaction clips.
- Homogeneous MP4 video: H.264, AAC, 1280×720 at 30 FPS.

Reaction clips can be MP4, MOV or WebM. FFmpeg converts them before
concatenating; image cards last 2 seconds each. A five-scene montage lasts
roughly the sum of five clip durations plus 10 seconds of visual context.

The sixth PR will connect these components in a CLI.

## Quality gates

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest
```

WPS v1.8.1 runs with no ignored WPS rules. Real FFmpeg integration tests use
synthetic image/video files, never copyrighted reaction video assets.
