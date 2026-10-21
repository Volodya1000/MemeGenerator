# Engineering rules for MemeGenerator

## Scope and design
- Runtime: Python 3.13. Prefer explicit contracts, small cohesive modules, and straightforward code over abstraction for its own sake.
- Apply SOLID, KISS, DRY, and YAGNI with judgment. Elegant Objects can inform encapsulation, but avoid Java-style one-method classes and abstraction without a real use case.
- Keep domain objects and invariants in `domain/`, use-case orchestration in `application/`, interfaces needed by use cases in `application/protocols/`, and adapters for storage, LLMs, images, and FFmpeg in `infrastructure/`.
- Infrastructure depends on application contracts; the application must not depend on concrete infrastructure classes.
- One file should have a clear primary responsibility. Do not add generic `common.py`, `utils.py`, or catch-all `models.py` modules.
- Use repository interfaces for catalog reads. An in-memory catalog is sufficient for tests; a future database adapter should not change the use cases.
- Use LiteLLM for provider-neutral model calls. Keep secrets in the environment or a gitignored `.env`; non-secret settings may be specified in YAML.
- Use Typer for user-facing commands. Keep CLI argument parsing separate from business logic.
- Prefer immutable or validated data structures and explicit dependency injection. Avoid hidden I/O at import time, singletons, service locators, unnecessary inheritance, and implicit fallback to network services.
- Extract constants only if they represent a coherent policy or are reused. Do not invent a global constants bucket.

## Python and quality
- Annotate public and internal functions, parameters, return values, and variable containers when inference is ambiguous.
- Avoid `Any`, untyped `dict`, and unjustified casts. Confine third-party untyped responses to adapter boundaries and validate them.
- Follow the strictest supported wemake-python-styleguide checks. Do not introduce global WPS suppressions or disable a rule merely to pass CI.
- Also run Ruff lint/format, strict mypy on source **and** tests where possible, pytest and coverage checks.
- Preserve explicit subprocess argument arrays, secure local paths, safe file formats, bounded downloads, and media provenance.

## Testing, following Vladimir Khorikov
- Prioritize protection against regressions, resistance to refactoring, fast feedback, and maintainability.
- Test externally observable results, domain invariants, output files and error conditions, not private call order or trivial getters.
- Prefer deterministic state/output-based tests. Use fakes for meaningful external boundaries (LLM, FFmpeg, clock, filesystem, network), not mocks of every internal collaborator.
- Keep unit tests independent of network services. Use synthetic media for FFmpeg integration tests and mark infrastructure-dependent tests explicitly.
- Test missing/duplicate/unsafe catalog entries, invalid LLM output, provider errors, invalid images, unavailable binaries, and unsuccessful render transactions.
- Coverage is a safety net, not an objective to optimize at the expense of assertions. Increase thresholds as meaningful behavioral coverage grows.

## PR discipline
- One clear architectural theme per PR; document migration implications.
- If changes affect stacked PRs, keep base branches consistent. Do not merge a dependent PR before its base.
- Confirm all checks succeed on the actual head commit before recommending merge.
- Never check in user-supplied movie clips, API keys, downloaded third-party content, or generated video.

## SQL storage and persistence
- Treat MemeRepositoryProtocol as the application query port; SQLAlchemy models, sessions, and DB URLs must not leak into domain or generation orchestration.
- Use SQLAlchemy 2.x sessions with explicit transaction boundaries; close sessions after operations.
- SQL credentials and connection URLs belong in environment variables, never checked-in YAML or generated video manifests.
- Use real SQLite-backed integration tests for repository state and transaction semantics, and PostgreSQL tests where a CI service is available; do not mock the ORM.
- Database schema initialization is explicit for local imports. Introduce migrations before production schema changes.

- Keep SQL writer operations behind a separate typed write port. A read-only repository interface should not grow mutating methods solely for one adapter.
- Use temporary SQLite databases for fast integration tests, an actual PostgreSQL service in CI, and verify durable reads, consistent contracts, and atomic rollback on failed writes.
- Shared fixtures belong in a local conftest.py near the tests that use them. Avoid global fixture collections without a clear responsibility.

## Current module boundaries
- Name contracts `*Protocol` and keep them under `application/protocols/`. Keep implementations named after their storage or provider semantics.
- SQLAlchemy lives under `persistence/sqlalchemy/`, not `infrastructure/`. Composition alone chooses concrete adapters; domain and application depend on no persistence packages.
- One root `GenerationSettings(BaseSettings)` with validated nested `DatabaseSettings` and `LLMSettings`. Never call `os.getenv` from adapters or use hand-written environment/YAML merges.
- Model JSON requests and manifests explicitly with Pydantic; prefer `model_dump_json` for serialization. Keep third-party request parameters and API schemas strictly typed.
- Use Tenacity only for transient external failures. Validation errors are deterministic failures, not a reason to retry.
- Apply import-linter contracts to guard the layering in CI. Mutation tests may be used selectively where they reveal defects in meaningful assertions.
