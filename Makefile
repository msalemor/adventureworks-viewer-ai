default:
	@echo "Please specify a target to build"

clean-py:
	rm -rf src/backend/wwwroot
	mkdir -p src/backend/wwwroot

clean-cs:
	rm -rf src/csbackend/wwwroot
	mkdir -p src/csbackend/wwwroot

build-ui-py: clean-py
	cd src/frontend && bun run prodpy
	cp -r src/frontend/dist/* src/backend/wwwroot

build-ui-cs: clean-cs
	cd src/frontend && bun run prodcs
	cp -r src/frontend/dist/* src/csbackend/wwwroot

TAG_NAME=alemoracr.azurecr.io/pyadventureviewer
TAG_VERSION=0.0.16
docker-build-py: build-ui-py
	cd src/backend && docker build -t $(TAG_NAME):$(TAG_VERSION) .

docker-run-py:
	cd src/backend && docker run --rm --env-file=.env -p 8060:80 $(TAG_NAME):$(TAG_VERSION)

TAG_NAME_CS=alemoracr.azurecr.io/csadventureviewer
TAG_VERSION_CS=0.0.1
docker-build-cs: build-ui-cs
	cd src/csbackend && docker build -t $(TAG_NAME_CS):$(TAG_VERSION_CS) .

docker-run-cs:
	cd src/csbackend && docker run --rm --env-file=.env -p 8070:80 $(TAG_NAME_CS):$(TAG_VERSION_CS)

REPO_NAME=alemoracr
docker-push-py:
	az acr login --name alemoracr
	docker push $(TAG_NAME):$(TAG_VERSION)

docker-push-cs:
	az acr login --name alemoracr
	docker push $(TAG_NAME_CS):$(TAG_VERSION_CS)
