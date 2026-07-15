PYTHON ?= .venv/Scripts/python
PIP ?= .venv/Scripts/pip
DBT ?= .venv/Scripts/dbt.exe
NPM ?= npm

.PHONY: install ingest venues-report dbt-build api frontend dev test lint typecheck build docker-build docker-run

install:
	$(PYTHON) -m venv .venv
	$(PIP) install -e ".[dev]"
	cd frontend && $(NPM) install

ingest:
	$(PYTHON) scripts/ingest.py

venues-report:
	$(PYTHON) scripts/build_full_venue_seed.py
	$(PYTHON) scripts/venues_report.py

dbt-build:
	set DUCKDB_PATH=data/worldcup.duckdb&& set MATCHES_PARQUET_PATH=data/working/matches.parquet&& $(DBT) build --project-dir analytics --profiles-dir analytics

api:
	$(PYTHON) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && $(NPM) run dev

dev:
	@echo "Run `make api` and `make frontend` in separate terminals"

test:
	$(PYTHON) -m pytest tests -q
	cd frontend && $(NPM) run test

lint:
	$(PYTHON) -m ruff check app tests scripts
	cd frontend && $(NPM) run lint

typecheck:
	$(PYTHON) -m mypy app

build: dbt-build
	cd frontend && $(NPM) run build

docker-build:
	docker build -t worldcup-travel-atlas .

docker-run:
	docker run --rm -p 10000:10000 -e PORT=10000 worldcup-travel-atlas
