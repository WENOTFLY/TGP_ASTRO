.PHONY: format lint type test build up

format:
	ruff --fix .
	black .

lint:
	ruff .
	make type

type:
	mypy --strict .

test:
	pytest --cov=app --cov-report=term-missing --cov-fail-under=90

build:
	docker-compose build

up:
	docker-compose up
