.PHONY: help install dev clean build up down logs restart train analyze test

help:
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make dev        - Install dev dependencies"
	@echo "  make clean      - Clean up cache and logs"
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start services with docker-compose"
	@echo "  make down       - Stop services"
	@echo "  make logs       - Show service logs"
	@echo "  make restart    - Restart services"
	@echo "  make train      - Train ML models"
	@echo "  make analyze    - Analyze training data"
	@echo "  make test       - Run tests"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy

clean:
	rm -rf cache/* logs/* __pycache__ *.pyc .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f ci-service

restart:
	docker-compose restart ci-service

train:
	@echo "Training ML models..."
	python quick_train.py train/data/processed_training_data.parquet ./models

analyze:
	@echo "Analyzing training data..."
	python analyze_data.py train/data/processed_training_data.parquet

test:
	pytest tests/ -v --cov=. --cov-report=term-missing

format:
	black *.py
	black tests/*.py 2>/dev/null || true

lint:
	flake8 *.py --max-line-length=100
	mypy *.py --ignore-missing-imports
