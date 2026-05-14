ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENV := $(ROOT)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy
PYTEST := $(VENV)/bin/pytest
LINT_IMPORTS := $(VENV)/bin/lint-imports

.PHONY: help venv install lint format fix types test imports check clean run hooks-run

help:
	@echo "targets:"
	@echo "  venv      create .venv (python3.12)"
	@echo "  install   pip install -e .[dev] + pre-commit install"
	@echo "  lint      ruff check + format --check"
	@echo "  format    ruff format (apply)"
	@echo "  fix       ruff check --fix + format (apply)"
	@echo "  types     mypy --strict"
	@echo "  test      pytest with coverage"
	@echo "  imports   lint-imports (Clean Arch contract)"
	@echo "  check     lint + types + test + imports"
	@echo "  clean     remove caches"
	@echo "  run       launch daemon (uvicorn)"
	@echo "  hooks-run run all pre-commit hooks across all files (occasional sweep)"

venv:
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip

install:
	$(PIP) install -e "$(ROOT)[dev]"
	env -C $(ROOT) $(VENV)/bin/pre-commit install

lint:
	env -C $(ROOT) $(RUFF) check colourlog tests
	env -C $(ROOT) $(RUFF) format --check colourlog tests

format:
	env -C $(ROOT) $(RUFF) format colourlog tests

fix:
	env -C $(ROOT) $(RUFF) check --fix colourlog tests
	env -C $(ROOT) $(RUFF) format colourlog tests

types:
	env -C $(ROOT) $(MYPY) colourlog tests

test:
	rm -f $(ROOT)/.coverage
	env -C $(ROOT) $(PYTEST)

imports:
	env -C $(ROOT) $(LINT_IMPORTS)

check: lint types test imports

clean:
	rm -rf $(ROOT)/.ruff_cache $(ROOT)/.mypy_cache $(ROOT)/.pytest_cache $(ROOT)/.coverage
	find $(ROOT) -type d -name __pycache__ -exec rm -rf {} +

run:
	COLOURLOG_LOG_FILE=$(ROOT)/var/log/colourlog.log $(PY) -m colourlog

hooks-run:
	env -C $(ROOT) $(VENV)/bin/pre-commit run --all-files
