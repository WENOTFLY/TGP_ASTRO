.PHONY: format lint type test build up

format:
	ruff check --fix .
	black .

lint:
	ruff check .
	make type

type:
	mypy --strict .

test:
	pytest

build:
	docker-compose build

up:
	docker-compose up
