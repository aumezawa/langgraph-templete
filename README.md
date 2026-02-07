# langgraph-template

## Requirements

- python 3.14 or later
- uv

## Setup

```shell
python -m venv .venv
.\.venv\Script\Activate.ps1

uv sync
```

## Run

```shell
uv run python -m cli.query -a <agent> -q <query> -m [single|single-stream]
```
or
```shell
uv run python -m cli.query -a <agent> -m [multi|multi-stream]
```

## Run A2A server

```shell
uv run python -m cli.run_server -a <agent> -m [blocking|non-blocking|streaming]
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
uv run mypy .
```