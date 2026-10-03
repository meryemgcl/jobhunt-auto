.PHONY: install test lint run clean build-fetcher data-report data-jobs data-runs data-trend data-companies data-export

install:
	python -m pip install -r requirements.txt -r requirements-dev.txt -r requirements-api.txt

test:
	pytest

lint:
	ruff check . --fix

run:
	python main.py

dashboard:
	python scripts/generate_static_dashboard.py --days 30 --output DASHBOARD.md

build-fetcher:
	cd services/go-fetcher && go build -o ../../bin/fetcher main.go

# ─── Veri Keşif Komutları ────────────────────────────────────────────────────
data-report:
	python scripts/data_explorer.py report

data-jobs:
	python scripts/data_explorer.py jobs --status sent --limit 50

data-runs:
	python scripts/data_explorer.py runs --last 20

data-trend:
	python scripts/data_explorer.py score-trend --days 30

data-companies:
	python scripts/data_explorer.py companies

data-unread:
	python scripts/data_explorer.py unread

data-export:
	python scripts/data_explorer.py export-csv --output exports/opportunities_$(shell date +%Y%m%d).csv
	python scripts/data_explorer.py export-json --output exports/opportunities_$(shell date +%Y%m%d).json
	@echo "Dışa aktarım tamamlandı: exports/"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf bin/

