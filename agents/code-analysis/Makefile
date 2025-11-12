PYTHON ?= python3
PIP_COMPILE ?= $(PYTHON) -m piptools compile

.PHONY: install install-dev lock lint format typecheck test run pre-commit

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -e .[dev]

lock:
	$(PIP_COMPILE) requirements.in --output-file requirements.txt

lint:
	ruff check src

format:
	black src tests

typecheck:
	mypy src

test:
	pytest -q

run:
	PYTHONPATH=src $(PYTHON) -m agent "Describe workspace"

pre-commit:
	pre-commit install --install-hooks
