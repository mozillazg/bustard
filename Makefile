.PHONY: help
help:
	@echo "tests"

.PHONY: tests
tests:
	@py.test --cov bustard tests --cov-report=term-missing
