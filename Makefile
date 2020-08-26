.PHONY: image

-include .env

branch ?= master
NAME_IMAGE ?= "$(CI_REGISTRY_IMAGE)"
TAG_IMAGE := branch-$(subst /,-,$(branch))

# We use :latest so we can use somewhere else, but it's the same as branch-master the other one is for CI
ifeq ($(branch), latest)
	TAG_IMAGE=latest
endif


## Make remote image form a branch make image branch=<branchName> (master default)
image: login build tag push

login:
	docker login -u gitlab-ci-token -p "$(CI_JOB_TOKEN)" "$(CI_REGISTRY)"

build: copy-app
	docker build -t $(NAME_IMAGE):$(TAG_IMAGE) .

push:
	docker push $(NAME_IMAGE):$(TAG_IMAGE)

tag:
	docker tag $(NAME_IMAGE):$(TAG_IMAGE) $(NAME_IMAGE):$(TAG_IMAGE)

copy-app:
	@ cd ..
	@ rm -rf __SOURCE_APP || true
	@ rsync \
			-avz \
			--exclude .git \
			--exclude .env \
			--exclude __SOURCE_APP \
			. __SOURCE_APP
	@ cd - > /dev/null

latest: login latest-tag
latest-tag:
	docker pull $(NAME_IMAGE):branch-master
	docker tag $(NAME_IMAGE):branch-master $(NAME_IMAGE):latest
	docker push $(NAME_IMAGE):latest

## Build image on local -> name nm-core:latest
local: copy-app
	@ docker build -t "$(NAME_IMAGE)" .
	@ rm -rf __SOURCE_APP || true
local: NAME_IMAGE = nm-core:latest

test: local
	# Keep -it because with colors it's better
	@ docker run \
			--rm \
			-it \
			--privileged \
			--volume $(PWD)/.env:/home/user/protonvpn-nm-core/.env \
			nm-core:latest \
			python3 -m pytest

# Build an image from your computer and push it to our repository
deploy-local: login-deploy build tag push

login-deploy:
	docker login -u "$(CI_DEPLOY_USER)" -p "$(CI_JOB_TOKEN)" "$(CI_REGISTRY)"

