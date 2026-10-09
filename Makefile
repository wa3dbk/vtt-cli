.PHONY: install test lint fmt update-goldens demo

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

fmt:
	ruff format .

update-goldens:
	pytest --update-goldens

demo:
	vtt-clean process samples/*.vtt -o out/ --format all
