all:
	@echo "nothing is done when 'all' is done, try make help"
help:	## show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

.PHONY: docker
docker:	## builds base docker images
	docker build -t t-ctr.otvl.org/debpy:3.13 . -f docker/Dockerfile.debpy
	docker build -t t-ctr.otvl.org/debpyv:3.13 . -f docker/Dockerfile.debpyv
	docker build -t t-ctr.otvl.org/ddpestores:0.1.3 . -f docker/Dockerfile.ddpestores
