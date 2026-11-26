---
name: python-coding-guidelines
description: >
  Modern Python (3.13+) coding standards for writing, reviewing or refactoring Python code.
  Use whenever creating or editing .py files, pyproject.toml, tests, CLIs, web APIs, data
  models or async code. Covers uv workspaces, ruff, type checking, pytest, pydantic,
  FastAPI, httpx, typer, logging, error handling and project layout.
---

# Python Coding Guidelines

Write code that is typed, small, explicit and easy to test. When these rules conflict
with the existing code in a file, follow the file's established style unless asked to
refactor, and mention the conflict.

## 1. Workflow (do this every time)

1. Read the surrounding module and its tests before editing.
2. Make the change in the smallest reasonable diff.
3. Run, in order, and fix what they report:
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   uv run ty check          # or: uv run pyright / uv run mypy, whichever the repo uses
   uv run pytest -q
   ```
4. Never claim code works without running it or its tests. Report failures verbatim.

## 2. Tooling and project setup

| Concern            | Use                                        | Avoid                              |
|--------------------|--------------------------------------------|------------------------------------|
| Env + deps         | `uv` (`uv add`, `uv sync`, `uv run`)       | bare `pip install`, requirements.txt as source of truth |
| Lint + format      | `ruff` (lint + format)                     | black + isort + flake8 stacks      |
| Type checking      | `ty`, `pyright` or `mypy --strict`         | untyped public functions           |
| Tests              | `pytest`, `pytest-asyncio`/`anyio`, `hypothesis` | `unittest` for new tests     |
| Build backend      | `uv_build` or `hatchling`                  | `setup.py`                         |
| Task running       | `uv run <cmd>`                             | activating venvs in scripts        |

- All config lives in `pyproject.toml`. Pin lower bounds (`>=`) in libraries; `uv.lock` pins apps.
- In a uv workspace, shared code goes in `packages/*`, deployables in `apps/*`. Reference
  members with `{ workspace = true }` in `[tool.uv.sources]`; never use relative path hacks
  or `sys.path` manipulation.
- Add a dependency with `uv add <pkg>` (or `uv add --package <member> <pkg>`), not by
  hand-editing the lock file. Dev tools go in `[dependency-groups] dev`.

Recommended ruff baseline:
```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "C4", "RUF", "PTH", "N", "S", "ASYNC", "PL", "TC"]
ignore = ["PLR2004"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004"]
```

## 3. Typing

- Annotate every function signature (params and return). Locals only when inference fails.
- Use built-in generics and `|`: `list[str]`, `dict[str, int]`, `str | None`.
  Never `List`, `Dict`, `Optional`, `Union`.
- Use PEP 695 syntax for generics and aliases:
  ```python
  type UserId = int
  type Result[T] = T | Exception

  def first[T](items: Sequence[T]) -> T | None:
      return items[0] if items else None
  ```
- Accept abstract types, return concrete ones: take `Iterable`/`Sequence`/`Mapping`
  (from `collections.abc`), return `list`/`dict`.
- Use `Protocol` for structural interfaces instead of ABCs when you only need a shape.
- Use `Literal` / `StrEnum` for closed sets of values, not bare strings.
- Use `@override` (from `typing`) on overridden methods, `Self` for fluent returns,
  `Final` for constants, `TypedDict` for typed dict payloads you do not own.
- `Any` is a last resort; prefer `object` when you only pass a value through.
- Imports used only for typing go under `if TYPE_CHECKING:`.

## 4. Data modelling

Pick the lightest tool that fits:

| Need                                               | Use                                  |
|----------------------------------------------------|--------------------------------------|
| Internal value object, no validation               | `@dataclass(frozen=True, slots=True, kw_only=True)` |
| Data crossing a trust boundary (HTTP, files, env, LLM output) | `pydantic.BaseModel` (v2)  |
| Settings / configuration                           | `pydantic_settings.BaseSettings`     |
| Fixed set of options                               | `enum.StrEnum` / `IntEnum`           |

- Default to immutable (`frozen=True`); use `dataclasses.replace` / `model_copy(update=...)`.
- Validate at the edges, trust types inside. Parse untrusted input once into a model,
  then pass the model around, not raw dicts.
- Pydantic v2 only: `model_validate`, `model_dump`, `field_validator`, `ConfigDict`.
  Never v1 APIs (`parse_obj`, `.dict()`, `@validator`, `class Config`).

## 5. Code structure and style

- Functions do one thing; aim for < 40 lines and <= 4 parameters. More? Group them into a
  dataclass or make trailing params keyword-only (`*,`).
- Prefer pure functions and composition. Use classes when there is state plus behaviour,
  not as namespaces.
- Inject dependencies (clients, clocks, repositories) through parameters or constructors;
  do not create them at import time. No work with side effects at module import.
- Early return over nested `if`. Use `match` for structural dispatch on shapes/variants.
- Comprehensions for simple transforms; a loop when there is more than one condition or
  side effect. Generators for large or streaming data.
- `pathlib.Path` for all filesystem work. Always pass `encoding="utf-8"` to
  `read_text`/`write_text`/`open` (Windows defaults differ).
- f-strings for formatting (but not inside logging calls - see section 7).
- Naming: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants,
  leading `_` for module-private. Names describe intent, not type (`users`, not `user_list`).
- Docstrings (Google style) on public modules, classes and functions whose behaviour is not
  obvious from name + types. Comments explain *why*, never *what*.
- No mutable default arguments; no wildcard imports; no `global`.

## 6. Errors

- Raise specific exceptions. Define a small hierarchy per package:
  ```python
  class FactoryError(Exception):
      """Base for all errors raised by this package."""

  class SkillNotFoundError(FactoryError):
      def __init__(self, name: str) -> None:
          super().__init__(f"skill not found: {name!r}")
          self.name = name
  ```
- Catch only what you can handle, as narrowly as possible. Never bare `except:`; never
  `except Exception: pass`. Re-raise with context: `raise AppError(...) from exc`.
- Do not use exceptions for normal control flow, and do not return error strings in place
  of raising.
- Use `with` / `contextlib` for every resource (files, locks, clients, sessions).
- Use `ExceptionGroup` / `except*` when handling errors from `TaskGroup`.

## 7. Logging and output

- Libraries: `logger = logging.getLogger(__name__)`; never configure logging or `print`.
- Apps: configure logging once at the entry point (stdlib `logging.config.dictConfig`, or
  `structlog` for JSON/structured logs).
- Lazy formatting: `logger.info("loaded %d skills", n)`, not f-strings.
- `logger.exception(...)` inside `except` to keep the traceback.
- Never log secrets, tokens, full request bodies or PII.

## 8. Async and concurrency

- Use `async` only for I/O-bound work and only when the call chain is async end to end.
  Never call blocking I/O (`requests`, `time.sleep`, sync DB drivers) inside `async def`;
  use `httpx.AsyncClient`, `asyncio.sleep`, or `await asyncio.to_thread(fn)`.
- Structured concurrency: `async with asyncio.TaskGroup() as tg:` instead of bare
  `create_task` / `gather`. Bound fan-out with `asyncio.Semaphore`.
- Timeouts on every network call: `async with asyncio.timeout(10):` or client timeouts.
- CPU-bound work: `concurrent.futures.ProcessPoolExecutor` (or free-threaded builds if the
  project targets them), not threads.

## 9. Framework defaults

Use these unless the project already chose otherwise:

- **HTTP client:** `httpx` (sync or async), one shared client per app, explicit `timeout=`,
  `raise_for_status()` or explicit status handling. Retries with `tenacity` / `stamina`.
- **Web API:** `FastAPI` + pydantic models for request/response, `Depends` for DI,
  `lifespan` context manager for startup/shutdown (not `@app.on_event`), `APIRouter` per
  feature. Run with `uvicorn`/`fastapi run`.
- **CLI:** `typer` (or `argparse` for zero-dependency tools). `main()` returns an exit code;
  guard with `if __name__ == "__main__": raise SystemExit(main())`. Expose via
  `[project.scripts]`.
- **Database:** `SQLAlchemy 2.0` typed ORM (`Mapped[...]`, `mapped_column`, `select()`)
  or `SQLModel`; migrations with `alembic`. Always parameterised queries.
- **Data frames:** `polars` for new code (lazy API for large data); `pandas` only where the
  ecosystem requires it.
- **Config/secrets:** `pydantic-settings` reading env / `.env`; `SecretStr` for secrets.
  Never hard-code secrets or commit `.env`.
- **LLM output / JSON from outside:** validate into a pydantic model before use.

## 10. Testing

- Tests live in `tests/` mirroring the package layout; file `test_<module>.py`,
  function `test_<behaviour>_<condition>`.
- One behaviour per test, Arrange / Act / Assert. Plain `assert`.
- Use fixtures for setup, `tmp_path` for files, `monkeypatch` for env, `pytest.mark.parametrize`
  for tables of cases, `pytest.raises(Err, match=...)` for errors.
- Mock at boundaries (network, clock, filesystem) only; prefer fakes over deep `MagicMock`
  chains. For HTTP use `respx` or `httpx.MockTransport`.
- Use `hypothesis` for parsers, serializers and pure functions with wide input spaces.
- New behaviour ships with tests; a bug fix ships with a test that failed before the fix.
- Keep tests fast and deterministic: no real network, no sleeps, fixed seeds.

## 11. Security

- Never use `eval`, `exec`, `pickle` on untrusted data, `yaml.load` (use `yaml.safe_load`),
  or `subprocess` with `shell=True` and interpolated input. Pass argument lists.
- Validate and normalise paths from users (`Path.resolve()` and check `is_relative_to`).
- Use `secrets` for tokens, `hashlib`/`hmac.compare_digest` for comparisons.
- Keep dependencies current; check with `uv lock --upgrade` + tests, and `pip-audit`.

## 12. Performance (only after measuring)

- Profile first: `cProfile`, `py-spy`, `pyinstrument`. Do not micro-optimise unmeasured code.
- Pick the right structure: `set`/`dict` for membership, `collections.deque` for queues,
  `heapq` for top-k, `functools.cache` for pure repeated calls.
- Stream large inputs with generators; avoid loading whole files when iterating lines works.

## 13. Review checklist

Before finishing, confirm:

- [ ] ruff format + ruff check + type checker + pytest all pass
- [ ] Every public function is typed; no new `Any`, no `# type: ignore` without a reason
- [ ] External input is validated into models at the boundary
- [ ] Resources use context managers; network calls have timeouts
- [ ] Errors are specific, chained with `from`, never swallowed
- [ ] No secrets, prints or debug leftovers; logging is lazy and PII-free
- [ ] Tests cover the new behaviour and the failure path
- [ ] Files read/written with `encoding="utf-8"`

## Example: idiomatic module

```python
"""Load agent skills from SKILL.md files."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

logger = logging.getLogger(__name__)


class SkillError(Exception):
    """Base error for skill loading."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Skill:
    name: str
    description: str
    path: Path


def parse_skill(path: Path) -> Skill:
    """Parse one SKILL.md file. Raises SkillError if the front matter is invalid."""
    text = path.read_text(encoding="utf-8")
    try:
        _, front, _ = text.split("---\n", 2)
        meta = yaml.safe_load(front) or {}
    except (ValueError, yaml.YAMLError) as exc:
        raise SkillError(f"invalid front matter in {path}") from exc

    match meta:
        case {"name": str(name), "description": str(description)}:
            return Skill(name=name, description=" ".join(description.split()), path=path)
        case _:
            raise SkillError(f"{path} needs string 'name' and 'description'")


def discover(roots: Iterable[Path]) -> dict[str, Skill]:
    """Return skills found under each root; earlier roots win on name clashes."""
    skills: dict[str, Skill] = {}
    for root in roots:
        for path in sorted(root.glob("*/SKILL.md")):
            try:
                skill = parse_skill(path)
            except SkillError:
                logger.warning("skipping invalid skill at %s", path, exc_info=True)
                continue
            skills.setdefault(skill.name, skill)
    return skills
```
