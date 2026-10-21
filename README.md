# MemeGenerator

Build themed MP4 reaction videos from an approved local collection of clips.
Each scene uses a contextual still image followed by a recorded reaction.

The project never downloads celebrity reaction videos, clones voices, or
generates a person's likeness. Supply clips you are authorized to use.

## Prerequisites

- Python 3.13, uv, FFmpeg and FFprobe available in PATH
- A curated JSON catalog referencing local video clips
- Either local contextual images or Wikimedia Commons images
- An optional LiteLLM-supported model for creative planning

## Install

```bash
uv sync --extra dev
cp assets/memes.example.json assets/memes.json
cp config.example.yaml config.yaml
cp .env.example .env
```

Put authorized reaction clips at the paths in `assets/memes.json`.
The example catalog does not ship any third-party media.

## Configure

Non-secret settings live in `config.yaml`:

```yaml
planner: llm
model: openai/qwen2.5-coder-14b-instruct
api_base: http://localhost:11434/v1
scenes: 5
catalog: assets/memes.json
output: output/result.mp4
images: commons
```

To use an OpenAI-compatible API, change `model` and `api_base`.
LiteLLM also supports providers such as Anthropic and local Ollama. Model
names should include the LiteLLM provider prefix, such as `openai/name`.

Secrets must be provided in the environment or a gitignored `.env`.
Use `MEMEGEN_API_KEY` or `OPENAI_API_KEY`. Environment variables
`MEMEGEN_MODEL` and `MEMEGEN_BASE_URL` override the corresponding
YAML settings. Never put credentials in committed YAML files.

## Run

```bash
uv run meme-generator generate --topic "Жизнь программиста" --config config.yaml
```

For a deterministic offline demonstration, use:

```yaml
planner: demo
images: local
image_dir: assets/context
scenes: 2
catalog: assets/memes.json
output: output/demo.mp4
```

Supply `assets/context/1.jpg`, `2.png`, etc. and run the same command.
The CLI supports `--topic`, `--config`, `--scenes`, and `--output`;
the remainder of the settings are explicit YAML keys.

The output includes `result.mp4`, `result.scenario.json` with the
validated scene plan, and `result.attribution.json` with image provenance.
Commons search is approximate; licenses and attribution must be reviewed.

## Architecture

- `domain/`: individual validated entities and business invariants.
- `application/ports/`: typed repository/planner/image/renderer contracts.
- `application/pipeline.py`: generation use case.
- `bootstrap.py` and `composition/catalog.py`: assemble concrete adapters.
- `infrastructure/`: JSON catalog, LiteLLM, image sources and FFmpeg.
- `config/`: validated YAML and environment loading.
- `cli.py`: Typer commands.
- `AGENTS.md`: full engineering, safety, and test standards.

Run quality checks with `uv run flake8 . --select WPS`,
`uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy src`, and `uv run pytest`.

## SQLAlchemy catalog backend

Choose your backend in `config.yaml`:

```yaml
catalog_backend: sqlalchemy
catalog: assets/memes.json
```

Provide the database URL through the environment or the gitignored
`.env` file (never in YAML):

```bash
MEMEGEN_DATABASE_URL=sqlite+pysqlite:///./memes.sqlite3
```

For PostgreSQL, install the optional driver with
`uv sync --extra postgres` and use an appropriate SQLAlchemy URL:

```bash
MEMEGEN_DATABASE_URL=postgresql+psycopg://user:password@localhost/memegen
```

Import clips **explicitly** before attempting SQL-backed generation:

```bash
uv run meme-generator catalog import --config config.yaml
uv run meme-generator generate --topic "Жизнь программиста" --config config.yaml
```

`catalog import` validates the JSON paths first and replaces the SQL
collection in one database transaction. It does not import on startup,
so an uninitialized database must be provisioned deliberately. JSON
remains the default for lightweight setups.

SQLAlchemy selects its database dialect from the URL. The application
uses only the `MemeRepository` port and can change storage without
modifying planning or video assembly. For production systems, manage
schema changes with Alembic rather than relying on `create_all`.

## Verification

The CI quality job runs complete FFmpeg integration tests, strict
mypy on source and tests, all WPS rules, Ruff, and an 85% branch-inclusive
coverage minimum. A separate job uses a real PostgreSQL service to
verify repository interoperability; default integration tests run with
real, isolated SQLite databases. Tests use behavior-based assertions
and database state rather than fragile SQL call-order mocks.

Catalog import preserves the original order of reactions. This matters
because deterministic planning must not change its selections merely
because the storage backend has changed.
