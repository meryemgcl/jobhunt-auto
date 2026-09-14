.PHONY: install test lint run clean

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

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
