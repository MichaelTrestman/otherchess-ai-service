.PHONY: setup test run

setup:
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest

run:
	python main.py
