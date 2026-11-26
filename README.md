# Thaniverse

Goodbye

## Structure

```
thaniverse/
├── pyproject.toml              # workspace root (not built), members = apps/*, packages/*
├── uv.lock                     # one lockfile for the whole workspace
├── .python-version
├── .env                        # local config (git-ignored)
├── apps/
│   └── factory/                # coding-agent CLI   package `factory`
│       ├── pyproject.toml
│       └── factory/
│           └── cli/            # agent.py, llm.py, main.py
└── packages/
     py_core/                # shared code  package `py-core` (import py_core)
        ├── pyproject.toml
        ├── __init__.py
        └── tools.py
```

Members are real packages installed in editable mode, so they import each other by package name.
Apps use `uv_build` with a flat layout. Libraries in `packages/` use hatchling so the folder itself is the package (no nested `py_core/py_core/`); see `packages/py_core/pyproject.toml`. A library's folder name must be a valid Python identifier (`py_core`, not `py-core`).

```python
from py_core.tools import TOOL_SCHEMAS
```

## Requirements

- Python 3.15 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync
```

The root depends on every member, so this installs the whole workspace into `.venv`.

Create a `.env` file in the repo root:

```env
MODEL_BASE_URL=
MODEL_API_KEY=
MODEL_NAME=
```

## Running

```sh
uv run factory                                   # console script from [project.scripts]
uv run python -m factory.cli.llm      # run a module directly
```

## Adding a member

1. Create the member:

   - **App** (`apps/<name>/`):

     ```sh
     uv init --package apps/<name>
     ```

     Run from the repo root, `uv init` detects the workspace. It creates a `src/` layout; move `src/<name>/` up one level, then add `[tool.uv.build-backend]` with `module-root = ""`.
   - **Library** (`packages/<name>/`, `<name>` a valid Python identifier): copy `packages/py_core/pyproject.toml`, change `name`, and set `"" = "<name>"` under `[tool.hatch.build.targets.wheel.sources]`. Put the `.py` files directly in the folder.
2. To use a library from another member, add it as a workspace dependency:

   ```sh
   uv add --package <app> <lib>
   ```

   Then add `<lib> = { workspace = true }` to `[tool.uv.sources]` in the root `pyproject.toml` (if `uv add` wrote it into the member instead, you can move it).
3. Add the new member to the root `dependencies` (and `[tool.uv.sources]`) so `uv sync` installs it.

## Dependencies

Add a dependency to the member that needs it:

```sh
uv add --package factory <dependency>
```