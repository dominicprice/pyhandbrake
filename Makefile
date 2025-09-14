.PHONY: lint
lint:
	poetry run mypy --check-untyped-defs src/handbrake
	poetry run mypy --check-untyped-defs tests

.PHONY: format
format:
	poetry run isort --tc --profile black .
	poetry run black .

.PHONY: test
test:
	poetry run coverage run -m pytest -vvv tests/ && poetry run coverage report


.PHONY: sdist
sdist:
	poetry build -f sdist

.PHONY: wheel
wheel:
	poetry build -f wheel
