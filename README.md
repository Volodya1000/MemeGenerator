# MemeGenerator

Generate a coherent themed video with **an image introducing each situation**
followed by a reaction from a **curated library of prerecorded video clips**.

A language model writes a narrative and selects an appropriate reaction using
only preapproved clip identifiers. Wikimedia Commons or preselected local
images supply scene context. FFmpeg assembles normalized H.264/AAC MP4.

The project does **not** synthesize a person's voice, generate deepfakes or
download celebrity reaction clips. Supply video clips you have permission to use.

## Requirements

- Python **3.13**
- FFmpeg and FFprobe on PATH
- An OpenAI-compatible chat completion endpoint for semantic planning
- Curated local video clips referenced in `assets/memes.json`
- Optional: preselected numbered scene images for offline generation

## Install

```bash
uv sync --extra dev
cp assets/memes.example.json assets/memes.json
mkdir -p assets/memes
```

Place legally obtained clips at the paths listed in `assets/memes.json`.
For every clip, register the **exact spoken phrase** and a stable `meme_id`.
The example is intentionally a placeholder; it cannot generate real video
until you supply at least one valid clip.

## Create a video with a local LLM

For example, use any Ollama/OpenAI-compatible server exposing
`/v1/chat/completions` and supporting `response_format=json_object`:

```bash
export MEMEGEN_BASE_URL=http://localhost:11434/v1
export MEMEGEN_MODEL=qwen2.5:14b
uv run python -m meme_generator generate \
  --topic "Жизнь программиста" \
  --scenes 5 \
  --catalog assets/memes.json \
  --output output/result.mp4
```

An OpenAI-compatible commercial endpoint can also be configured with
`MEMEGEN_BASE_URL`, `MEMEGEN_MODEL` and `OPENAI_API_KEY`.
The API key is never included in the generated artifact manifest.

## Fully offline montage

Use the deterministic, non-LLM planner and numbered local pictures:

```bash
mkdir -p assets/context
# Supply assets/context/1.jpg, 2.png, etc. yourself.
uv run python -m meme_generator generate \
  --topic "Software development" \
  --scenes 2 \
  --planner demo \
  --images local \
  --image-dir assets/context \
  --output output/demo.mp4
```

Demo mode exists to verify the pipeline, not to produce creative scenarios.

## Output

- `result.mp4`: image/context card for 2 seconds, then clip, in scene order.
- `result.scenario.json`: exact validated LLM scene plan.
- `result.attribution.json`: image queries, source URLs and license names.

FFmpeg produces 1280×720, 30 FPS H.264 video with AAC audio. Clips without
an audio track gain a silent one so concatenation works consistently.

Wikimedia Commons image matches use a basic text score, not visual recognition.
For high-quality precise scenes, preselect and use `--images local`.
Always verify individual Commons image licenses and any attribution terms.

## Repository structure

```text
src/meme_generator/
  domain/models.py              validated models and invariants
  application/planning.py       LLM + deterministic planner
  application/pipeline.py       orchestration and provenance
  infrastructure/catalog.py     safe local meme catalog
  infrastructure/media_probe.py FFprobe
  infrastructure/images.py      Commons and local image providers
  infrastructure/rendering.py   FFmpeg normalization and concat
  cli.py                        command-line interface
tests/                          unit and actual FFmpeg integration
```

## Quality

`wemake-python-styleguide==1.8.1` with **all WPS rules enabled and no WPS
ignore rules**. Complemented by broad Ruff rules, strict mypy and pytest.

```bash
uv run ruff check .
uv run ruff format --check .
uv run flake8 . --select WPS
uv run mypy src
uv run pytest
```

## Contributing

Use PRs with passing checks. Keep third-party clips and downloaded media out
of version control. Do not confuse passing validation with being funny:
LLM scenario quality and Commons image relevance require human evaluation.
