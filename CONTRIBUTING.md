# Contributing to mtk

Thanks for your interest in contributing! `mtk` is a multi-platform mobile pentesting toolkit. Android/APK support is available today; iOS/IPA analysis and broader device management are on the [roadmap](README.md#roadmap--planned) — contributions toward those are especially welcome.

## Development Setup

```bash
# Install with dev dependencies (uses uv)
uv sync --group dev
```

External tools (`adb`, `apktool`, `jadx`, `APKEditor`) are only needed at runtime for the commands that use them — see the [README](README.md#requirements).

## Project Layout

```
src/mtk/
├── cli/          # Typer commands — argument parsing and rich output only
├── core/         # Business logic — importable as a library
├── models/       # Pydantic v2 data models
├── utils/        # Shared utilities: deps checker, output helpers, process wrapper
└── exceptions.py # Typed exception hierarchy
```

Key constraints to respect:

- `cli/` **never** contains business logic — it only calls into `core/`.
- All subprocess invocations go through `utils/process.py` (`run_tool()`).
- External tool requirements are checked at command entry via `utils/deps.py` (`require()`).
- All exceptions inherit from `MTKError`.

## Validation

There is no automated test suite. Before opening a PR, run the full validation trio and confirm the CLI still works:

```bash
ruff check src/mtk/        # lint (strict rule set)
mypy src/mtk/              # type check (strict mode)
uv run mtk --help          # smoke test the CLI
```

All new code must be fully typed — mypy runs in strict mode.

## Commits

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/). See [.github/COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) for the full format.

- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- **Scopes** (when applicable): `cli`, `core`, `models`, `utils`, `deps`, `release`
- Header length is capped at 72 characters.

Set up the commit-message hook so violations are caught locally:

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
```

## Pull Requests

1. Branch off `main`.
2. Make your change and run the validation trio above.
3. Use conventional-commit messages.
4. Open a PR with a clear description of the change and how you verified it.
