# MemeGenerator

Build themed MP4 reaction videos from an approved local collection of clips.
Each scene uses a contextual still image followed by a recorded reaction.

The generator uses local, approved reaction clips and never clones voices or
creates a person's likeness. An **optional** separate asset importer can
download seven curated clips, but this does not grant redistribution rights.

## Prerequisites

- Python 3.13, uv, FFmpeg and FFprobe available in PATH
- A curated JSON catalog referencing local video clips
- Either local contextual images or Wikimedia Commons images
- An optional LiteLLM-supported model for creative planning

## Install

```bash
uv sync --extra dev
uv run meme-assets --download
cp config.example.yaml config.yaml
cp .env.example .env
```

The importer writes `assets/catalog.json` with video paths relative to the
catalog directory. Source MP4s and normalized video binaries are ignored by Git.
For a purely self-supplied catalog, copy `assets/memes.example.json` and set
`catalog` in YAML to the copied file.

## Configure

Non-secret settings live in `config.yaml`:

```yaml
planner: llm
llm:
  model: openai/qwen2.5-coder-14b-instruct
  api_base: http://localhost:11434/v1
  retry_attempts: 3
database:
  backend: json
scenes: 5
catalog: assets/catalog.json
output: output/result.mp4
images: commons
```

To use an OpenAI-compatible API, change `model` and `api_base`.
LiteLLM also supports providers such as Anthropic and local Ollama. Model
names should include the LiteLLM provider prefix, such as `openai/name`.

Secrets must be provided in the environment or a gitignored `.env`.
Use `MEMEGEN_LLM__API_KEY` for hosted models.
Nested environment overrides such as `MEMEGEN_LLM__MODEL`,
`MEMEGEN_LLM__API_BASE`, and `MEMEGEN_DATABASE__URL` override
non-secret YAML defaults. Pydantic Settings reads `.env` automatically. Never put credentials in committed YAML files.

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
catalog: assets/catalog.json
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
- `application/protocols/`: typed repository/planner/image/renderer contracts.
- `application/pipeline.py`: generation use case.
- `bootstrap.py` and `composition/catalog.py`: assemble concrete adapters.
- `infrastructure/`: in-memory catalog, LiteLLM, images and FFmpeg.
- `persistence/sqlalchemy/`: SQLAlchemy 2.x tables, sessions and repository.
- `config/`: one nested Pydantic Settings root for YAML, dotenv and env.
- `cli.py`: Typer commands.
- `AGENTS.md`: full engineering, safety, and test standards.

Run quality checks with `uv run flake8 . --select WPS`,
`uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy src`, and `uv run pytest`.

## SQLAlchemy catalog backend

Choose your backend in `config.yaml`:

```yaml
database:
  backend: sqlalchemy
catalog: assets/catalog.json
```

Provide the database URL through the environment or the gitignored
`.env` file (never in YAML):

```bash
MEMEGEN_DATABASE__URL=sqlite+pysqlite:///./memes.sqlite3
```

For PostgreSQL, install the optional driver with
`uv sync --extra postgres` and use an appropriate SQLAlchemy URL:

```bash
MEMEGEN_DATABASE__URL=postgresql+psycopg://user:password@localhost/memegen
```

Apply database schema migrations and then import approved clips **explicitly**:

```bash
uv run alembic upgrade head
```

Once the schema is at its latest revision, import clips:

```bash
uv run meme-generator catalog import --config config.yaml
uv run meme-generator generate --topic "Жизнь программиста" --config config.yaml
```

`catalog import` validates the JSON paths first and replaces the SQL
collection in one database transaction. It does not import on startup,
so an uninitialized database must be provisioned deliberately. JSON
remains the default for lightweight setups.

SQLAlchemy selects its database dialect from the URL. The application
uses only the `MemeRepositoryProtocol` port and can change storage without
modifying planning or video assembly. For production systems, manage
schema changes with the included Alembic revisions. Production imports do
not create tables implicitly, and migration downgrades remain explicit.

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

## Storage and architecture guarantees

`InMemoryMemeRepository` is the validated in-memory implementation;
`SqlAlchemyMemeRepository` implements the same
`MemeRepositoryProtocol`. Catalog import uses a separate
`CatalogWriterProtocol`. The database driver can be changed via the
SQLAlchemy URL without modifying business logic.

The source-of-truth settings class is
`meme_generator.config.settings.GenerationSettings`. Nested
`LLMSettings` and `DatabaseSettings` are validated Pydantic models.
Precedence is environment, dotenv, explicitly selected YAML, then defaults.
Database URLs and LLM keys are rejected in YAML and use `SecretStr` so
they are masked from normal model representations.

LLM requests and image search parameters are typed Pydantic models.
The LLM planner retries transient connection, rate-limit, timeout, and
availability errors with Tenacity exponential backoff (default 3
attempts, configurable through `llm.retry_attempts`); it does not
retry malformed JSON or hallucinated meme identifiers. Prompts reside
in the dedicated `infrastructure/prompts/` package.

Scenario and attribution JSON manifests are generated with
`model_dump_json` from validated Pydantic objects. Run
`uv run lint-imports` to enforce architecture boundaries before
committing.

## Curated meme media importer and smoke acceptance

The `meme-assets` entrypoint from the consolidated project downloads and
normalizes the seven independently reviewed reactions. Downloads are opt-in:

```bash
uv sync --extra dev
uv run meme-assets --download
```

Run `uv run meme-assets` without `--download` to revalidate already
available local originals with no network access. The generated file
`assets/catalog.json` is compatible with `InMemoryMemeRepository.from_json`
when the configured catalog path is `assets/catalog.json`.

For a fully offline functional test, set `planner: demo`, `images: local`,
`image_dir: assets/context` and supply your own `1.png` context image.
Then run `uv run meme-generator generate --topic 'Demo' --config config.yaml`.

The integration suite also executes importer, Pydantic catalog validation,
real FFmpeg encoding and generation in one synthetic-video end-to-end test.
The separate manual `Real meme media smoke test` workflow may re-fetch the
real clips, verify pinned SHA-256 checksums, and report only technical metadata.
Never commit source or normalized videos; see `docs/meme-assets.md` for the
source manifest and permissions caveats.
