all:
	@echo "nothing is done when 'all' is done, try make help"
help:	## show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

VENV := $(shell if [ -z "${VENV}" ] ; then echo /local/venvs/c01-general ; else echo ${VENV} ; fi)
CTR_URL := $(shell if [ -z "${CTR_URL}" ] ; then echo t-ctr.otvl.org ; else echo ${CTR_URL} ; fi)

.PHONY: venv
venv:	## create a virtualenv and install dependencies
venv: export PIP_NO_CACHE_DIR=1
venv: export PIPENV_VERBOSITY=-1
venv:
	virtualenv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt -r requirements-dev.txt

.PHONY: qa
qa: export PYTEST_FAST=1
qa:	## launch QA tests
	$(VENV)/bin/flake8 src
	@echo skip $(VENV)/bin/pytest src/
	$(VENV)/bin/coverage run --source=src/ -m pytest src/
	$(VENV)/bin/coverage report
	$(VENV)/bin/mypy src

.PHONY: build
build:	## builds a python package
	$(VENV)/bin/python -m build -o /tools/pip_repo/otvl-general

.PHONY: grpc-code
grpc-code:	## generate grpc code from proto files
	$(VENV)/bin/python -m grpc_tools.protoc -Iotvl_general/utils=src/protos --python_out=src --pyi_out=src --grpc_python_out=src src/protos/estore.proto
	$(VENV)/bin/python -m grpc_tools.protoc -Iotvl_general/utils=src/protos --python_out=src --pyi_out=src --grpc_python_out=src src/protos/stfl.proto
	$(VENV)/bin/python -m grpc_tools.protoc -Iotvl_general/utils=src/protos --python_out=src --pyi_out=src --grpc_python_out=src src/protos/ope.proto

.PHONY: dkbp
dkbp: export DK_IMG=workflow-task:0.13
dkbp:	## docker build and push
	docker build -t $(CTR_URL)/${DK_IMG} .
	docker push $(CTR_URL)/${DK_IMG}

.PHONY: mypy
mypy:	## launch QA tests on mypy only
	$(VENV)/bin/mypy src

.PHONY: coverage
coverage: export PYTEST_FAST=1
coverage:	## launch QA tests for HTML coverage only
	$(VENV)/bin/coverage run --source=src/ -m pytest src/
	$(VENV)/bin/coverage html

.PHONY: runs
runs: export PYTHONPATH=src
runs:	## run the grpc server
	$(VENV)/bin/python -m otvl_general.cmd.sfe_svr -p 8181 --db-server t-db-pgs -d estore_c01_main_test --s3-profile otvl-tests -b otvl-tests

.PHONY: runc1
runc1: export PYTHONPATH=src
runc1:	## run the grpc client1
	$(VENV)/bin/python -m otvl_general.utils.estore_client -p 8181 -c cat-cli1 --drop

.PHONY: runc2
runc2: export PYTHONPATH=src
runc2:	## run the grpc client2
	$(VENV)/bin/python -m otvl_general.utils.estore_client -p 8181 -c cat-cli2 --no-drop

.PHONY: runco
runco: export PYTHONPATH=src
runco:	## run the grpc ope client
	$(VENV)/bin/python -m otvl_general.cmd.sfe_ope_cli -p 8181 --ready
	$(VENV)/bin/python -m otvl_general.cmd.sfe_ope_cli -p 8181 --version
	$(VENV)/bin/python -m otvl_general.cmd.sfe_ope_cli -p 8181 --shutdown 2

.PHONY: test-estore
test-estore: export PYTEST_FAST=1
test-estore:	## launch QA tests on pytest estore only
	$(VENV)/bin/pytest \
		src/otvl_general/utils/test_estore.py

.PHONY: test-estoredb
test-estoredb:	## launch QA tests on pytest estoredb only
	$(VENV)/bin/pytest \
		src/otvl_general/utils/test_estoredb.py

.PHONY: test-stfl
test-stfl:	## launch QA tests on pytest stfl only
	$(VENV)/bin/pytest \
		src/otvl_general/utils/test_stfl.py

.PHONY: test-ope
test-ope:	## launch QA tests on pytest ope only
	$(VENV)/bin/pytest \
		src/otvl_general/utils/test_ope.py
