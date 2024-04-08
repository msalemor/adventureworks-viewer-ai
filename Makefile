default:
	@echo "Please specify a target to build"

clean:
	rm -rf src/backend/wwwroot
	mkdir -p src/backend/wwwroot

build-ui: clean
	cd src/frontend && bun run prod
	cp -r src/frontend/dist/* src/backend/wwwroot

TAG_NAME=alemoracr.azurecr.io/pyadventureviewer
TAG_VERSION=0.0.10
docker-build: build-ui
	cd src/backend && docker build -t $(TAG_NAME):$(TAG_VERSION) .

docker-run:
	cd src/backend && docker run --rm --env-file=.env -p 8080:80 $(TAG_NAME):$(TAG_VERSION)

REPO_NAME=alemoracr
docker-push:
	az acr login --name alemoracr
	docker push $(TAG_NAME):$(TAG_VERSION)