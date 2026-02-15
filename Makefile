.PHONY: help install test lint format type-check pre-commit clean dev check test-watch

help:
	@echo "B2B Dashboard - Comandos disponíveis:"
	@echo ""
	@echo "  make install         - Instalar dependências"
	@echo "  make install-dev     - Instalar com ferramentas de dev"
	@echo "  make test            - Rodar testes"
	@echo "  make test-cov        - Testes com cobertura"
	@echo "  make test-watch      - Rodar testes em watch mode"
	@echo "  make lint            - Rodar linter (pylint)"
	@echo "  make format          - Formatar código (black + isort)"
	@echo "  make format-check    - Verificar formatação"
	@echo "  make type-check      - Type checking (mypy)"
	@echo "  make pre-commit      - Rodar pre-commit hooks"
	@echo "  make check           - Quick check (format + lint)"
	@echo "  make dev             - Full dev check (format + lint + type-check + test)"
	@echo "  make run             - Executar dashboard"
	@echo "  make clean           - Limpar cache e artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-watch:
	pytest tests/ -v --watch

lint:
	pylint src/ dashboards/ --exit-zero

format:
	black src/ dashboards/ tests/
	isort src/ dashboards/ tests/

format-check:
	black --check src/ dashboards/ tests/
	isort --check-only src/ dashboards/ tests/

type-check:
	mypy src/ --ignore-missing-imports

check:
	black --check src/ dashboards/ tests/
	isort --check-only src/ dashboards/ tests/
	pylint src/ dashboards/ --exit-zero

dev: format type-check lint test-cov
	@echo "✅ All checks passed!"

pre-commit:
	pre-commit run --all-files

run:
	cd dashboards && streamlit run app.py

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .mypy_cache -exec rm -r {} +
	find . -type d -name htmlcov -exec rm -r {} +
	find . -type f -name .coverage -delete
