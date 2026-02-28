all:
	@echo "nothing is done when 'all' is done, try make help"
help:	## show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

VENV := $(shell if [ -z "${VENV}" ] ; then echo /local/venvs/ddpbasics ; else echo ${VENV} ; fi)
PYPIF := $(shell if [ -z "${PYPIF}" ] ; then echo /tools/pip_repo/ddpbasics ; else echo ${PYPIF} ; fi)

.PHONY: venv
venv:	## create a virtualenv and install dependencies
venv: export PIP_NO_CACHE_DIR=1
venv: export PIPENV_VERBOSITY=-1
venv:
	virtualenv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt -r requirements-dev.txt

.PHONY: qa
qa:	## launch QA tests
	$(VENV)/bin/flake8 src
	@echo skip $(VENV)/bin/pytest src/
	$(VENV)/bin/coverage run --source=src/ -m pytest src/
	$(VENV)/bin/coverage report
	$(VENV)/bin/mypy src

.PHONY: build
build:	## builds a python package
	$(VENV)/bin/python -m build -o $(PYPIF)

.PHONY: pytest
pytest:	## launch QA tests with pytest only
	$(VENV)/bin/pytest src/

.PHONY: pytest-1
pytest-1:	## launch QA tests with pytest selection only
	$(VENV)/bin/pytest src/ddpbasics/test_s3utils.py

.PHONY: mypy
mypy:	## launch QA tests on mypy only
	$(VENV)/bin/mypy src

.PHONY: coverage
coverage:	## launch QA tests for HTML coverage only
	$(VENV)/bin/coverage run --source=src/ -m pytest src/
	$(VENV)/bin/coverage html
