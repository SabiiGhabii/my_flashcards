.PHONY: test lint format install-dev clean

# Install development dependencies
install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Run core tests
test:
	python -m pytest tests/test_formatter_service_facade.py tests/test_card_type_registry.py tests/test_srs_factory.py tests/test_card_service.py -v

# Run all tests
test-all:
	python -m pytest tests/ -v

# Run tests with coverage
test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the application
run:
	python main.py

# Quick development check
check: format lint test
