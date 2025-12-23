# langgraph-template

## Requirements

- python 3.11 or later
- uv

## Setup

```shell
python -m venv .venv
.\.venv\Script\Activate.ps1

uv sync
```

## Run

```shell
uv run python ./app/chatbot.py
```

## Debug

### Linter

```shell
uv run ruff check
uv run ruff check --fix
```

### Formatter

```shell
uv run ruff format --check --diff
uv run ruff format
```

### Type Checking

```shell
uv run mypy <file.py>
```