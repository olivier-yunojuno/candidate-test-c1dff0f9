UV ?= uv # we'll assume that uv is somewhere in the developer's PATH, but this can be changed

.DEFAULT_GOAL := help

.PHONY: help
help:
# @link https://github.com/marmelab/javascript-boilerplate/blob/master/makefile
	@grep -P '^[.a-zA-Z/_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: python_version ?= 3.11
install: poetry_version ?= 1.8.5
install: uv_check
	${UV} venv --python ${python_version}
	${UV} tool run 'poetry==${poetry_version}' install
	${UV} run pre-commit install

.PHONY: test
test: pytest_args ?=
test:
	${UV} run pytest ${pytest_args}

.PHONY: format
format: black_args ?=
format: isort_args ?=
format:
	${UV} run black ${black_args} tests/ visitors/
	${UV} run isort ${isort_args} tests/ visitors/

.PHONY: uv_check
uv_check:
	@if ! type ${UV} >/dev/null 2>&1 ; then \
		echo "⚠️ This Makefile relies on uv, but uv doesn't seem to be installed."; \
 		echo "Please install it following these instructions: https://docs.astral.sh/uv/"; \
		exit 1; \
	fi
