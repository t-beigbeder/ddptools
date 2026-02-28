all:
	@echo "nothing is done when 'all' is done, try make help"
help:	## show this help
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

.PHONY: docker
docker:	## builds base docker images
	docker build -t $(V_CTR_PFX)debpy:$(V_DEBPY_V) . -f docker/Dockerfile.debpy
	docker build -t $(V_CTR_PFX)debpyv:$(V_DEBPY_V) . -f docker/Dockerfile.debpyv
	docker build \
		--build-arg V_DDPT_V=$(V_DDPT_V) \
		--build-arg DEBPYV_IMAGE=$(V_CTR_PFX)debpyv:$(V_DEBPY_V) \
		-t $(V_CTR_PFX)ddpestores-dev:$(V_DDPT_V) \
		. -f docker/Dockerfile.ddpestores-dev
	docker build \
		--build-arg V_DDPT_V=$(V_DDPT_V) \
		--build-arg DEBPY_IMAGE=$(V_CTR_PFX)debpy:$(V_DEBPY_V) \
		--build-arg DEBPYV_IMAGE=$(V_CTR_PFX)debpyv:$(V_DEBPY_V) \
		-t $(V_CTR_PFX)ddpestores:$(V_DDPT_V) \
		. -f docker/Dockerfile.ddpestores
	docker push $(V_CTR_PFX)ddpestores:$(V_DDPT_V)
	docker build \
		--build-arg V_DDPT_V=$(V_DDPT_V) \
		--build-arg DEBPY_IMAGE=$(V_CTR_PFX)debpy:$(V_DEBPY_V) \
		--build-arg DDPESTORES_DEV_IMAGE=$(V_CTR_PFX)ddpestores-dev:$(V_DDPT_V) \
		-t $(V_CTR_PFX)ddpestores2:$(V_DDPT_V) \
		. -f docker/Dockerfile.ddpestores2
	docker build \
		--build-arg V_DDPT_V=$(V_DDPT_V) \
		--build-arg DEBPYV_IMAGE=$(V_CTR_PFX)debpyv:$(V_DEBPY_V) \
		-t $(V_CTR_PFX)ddpestorec-dev:$(V_DDPT_V) \
		. -f docker/Dockerfile.ddpestorec-dev
	docker build \
		--build-arg V_DDPT_V=$(V_DDPT_V) \
		--build-arg DEBPY_IMAGE=$(V_CTR_PFX)debpy:$(V_DEBPY_V) \
		--build-arg DEBPYV_IMAGE=$(V_CTR_PFX)debpyv:$(V_DEBPY_V) \
		-t $(V_CTR_PFX)ddpestorec:$(V_DDPT_V) \
		. -f docker/Dockerfile.ddpestorec
	docker push $(V_CTR_PFX)ddpestorec:$(V_DDPT_V)
