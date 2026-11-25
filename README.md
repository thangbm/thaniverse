# Thaniverse

A [uv](https://docs.astral.sh/uv/) workspace monorepo. Every directory under `src/` is a standalone application with its own `pyproject.toml` and dependencies.

## Structure

```
thaniverse/
├── pyproject.toml        # virtual root, workspace members = ["src/*"]
├── uv.lock
├── .python-version
├── .env                  # local config (git-ignored)
└── src/
    └── cli/              # coding-agent CLI (thaniverse-cli)
        ├── pyproject.toml
        ├── agent.py
        ├── llm.py
        ├── main.py
        └── tools.py
```

`src/` contains applications only (`cli`, and later `api`, `desktop`, ...). The root is a virtual project, so it has no code or dependencies of its own.

Apps are not built as packages (`package = false`). They are run as scripts, so modules inside an app import each other directly (for example `from tools import TOOL_SCHEMAS`).

## Requirements

- Python 3.15 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync --all-packages
```

Create a `.env` file in the repo root:

```env
MODEL_BASE_URL=
MODEL_API_KEY=
MODEL_NAME=
```

## Running

Use `--package` to pick the app whose environment to use:

```sh
uv run --package thaniverse-cli python src/cli/llm.py
```

## Adding an application

1. Create `src/<name>/pyproject.toml`:

   ```toml
   [project]
   name = "thaniverse-<name>"
   version = "0.1.0"
   requires-python = ">=3.15"
   dependencies = []

   [tool.uv]
   package = false
   ```

2. Add the app's code in `src/<name>/`.
3. Run `uv sync --all-packages`. The `src/*` workspace glob picks the new app up automatically.
4. Run it with `uv run --package thaniverse-<name> python src/<name>/<entry>.py`.

## Dependencies

Add dependencies to the app that needs them:

```sh
uv add --package thaniverse-cli <dependency>
```
