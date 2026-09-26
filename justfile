set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

format:
	uv run --no-project --with ruff ruff format tools/jev.py tools/tests

lint:
	uv run --no-project --with ruff ruff check tools/jev.py tools/tests
	uv run --no-project --with mypy mypy tools/jev.py

test:
	uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider -W error tools/tests
