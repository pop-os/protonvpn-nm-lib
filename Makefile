.PHONY: image


branch ?= master
NAME_IMAGE ?= gitlab.protontech.ch:4567/deploy-app/fe-scripts
TAG_IMAGE := branch-$(subst /,-,$(branch))

# We use :latest so we can use somewhere else, but it's the same as branch-master the other one is for CI
ifeq ($(branch), latest)
	TAG_IMAGE=latest
endif


## Make remote image form a branch make image branch=<branchName> (master default)
image: login copy-scripts build tag push

login:
	docker login -u gitlab-ci-token -p "$(CI_JOB_TOKEN)" "$(CI_REGISTRY)"

push:
	docker push $(NAME_IMAGE):$(TAG_IMAGE)

tag:
	docker tag $(NAME_IMAGE):$(TAG_IMAGE) $(NAME_IMAGE):$(TAG_IMAGE)

latest: login latest-tag
latest-tag:
	docker pull $(NAME_IMAGE):branch-master
	docker tag $(NAME_IMAGE):branch-master $(NAME_IMAGE):latest
	docker push $(NAME_IMAGE):latest

build:
	@ docker build -t nm-core:latest .

test: build
	@ docker run --rm -u user --privileged --volume $(PWD):/home/user/protonvpn-nm-core nm-core:latest
## Make local image to test

local: copy-scripts local-image

local-image: SHELL:=/bin/bash
local-image:
	@ cd image && docker build -t $(NAME_IMAGE) .
local: NAME_IMAGE = deploy-app/fe-scripts

deploy-local: login-deploy copy-scripts build tag push

login-deploy:
	docker login -u "$(CI_DEPLOY_USER)" -p "$(CI_JOB_TOKEN)" "$(CI_REGISTRY)"

