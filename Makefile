default:
	@echo "Please specify a target to build"

clean:
	rm -rf src/backend/wwwroot
	mkdir -p src/backend/wwwroot

build-ui:
	cd src/frontend && bun run build
	cp -r src/frontend/dist/* src/backend/wwwroot

