default:
	@echo "Please specify a target to build"

clean:
	rm -rf src/backend/wwwroot
	mkdir -p src/backend/wwwroot

build-ui: clean
	cd src/frontend && bun run build
	cp -r src/frontend/dist/* src/backend/wwwroot

TAG_NAME=alemoracr.azurecr.io/adventureviewer
TAG_VERSION=0.0.0
docker-build: build-ui
	cd src/backend && docker build -t $(TAG_NAME):$(TAG_VERSION) .

docker-run:
	cd src/backend && docker run --rm --env-file=.env -p 8080:80 $(TAG_NAME):$(TAG_VERSION)