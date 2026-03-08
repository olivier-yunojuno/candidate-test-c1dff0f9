# we'll assume that uv is somewhere in the developer's PATH, but this can be changed:
UV ?= uv

PYTHON_BINARIES ?= .venv/bin

.DEFAULT_GOAL := help

.PHONY: help
help:
# @link https://github.com/marmelab/javascript-boilerplate/blob/master/makefile
	@grep -P '^[.a-zA-Z/_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: poetry_version ?= 1.8.5
install: uv_check .venv ## Install Python dependencies with Poetry, and install pre-commit
	${UV} tool run 'poetry==${poetry_version}' install
	${PYTHON_BINARIES}/pre-commit install

.PHONY: test
test: pytest_args ?= ## Run the test suite, powered by Pytest
test:
	@${PYTHON_BINARIES}/pytest ${pytest_args}

.PHONY: code-quality
code-quality: fmt lint mypy ## Run all the code quality tools

# Let's reflect the "fmt", "lint" and "mypy" Tox environments
.PHONY: fmt
fmt: black_args ?= --target-version py310
fmt: isort_args ?=
fmt: ## Run Black and isort
	@${PYTHON_BINARIES}/black ${black_args} tests/ visitors/
	@${PYTHON_BINARIES}/isort ${isort_args} tests/ visitors/

.PHONY: lint
lint: flake8_args ?=
lint: ## Run Flake8
	@${PYTHON_BINARIES}/flake8 ${flake8_args}

.PHONY: mypy
mypy: mypy_args ?=
mypy: ## Run MyPy
	@${PYTHON_BINARIES}/mypy ${mypy_args} visitors/

.PHONY: uv_check
uv_check: # internal target, doesn't need documentation
	@if ! type ${UV} >/dev/null 2>&1 ; then \
		echo "⚠️ This Makefile relies on uv, but uv doesn't seem to be installed."; \
 		echo "Please install it following these instructions: https://docs.astral.sh/uv/"; \
		exit 1; \
	fi

.venv: python_version ?= 3.10
.venv: # internal target, doesn't need documentation
	${UV} venv --python ${python_version}
