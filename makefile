OPENAPI_GENERATOR_VERSION ?= v7.25.0
OPENAPI_SPEC ?= $(shell find openapi -maxdepth 1 -type f -name 'firefly-iii-*-v1.yaml' | sort -V | tail -1)

.PHONY: openapi-gen openapi-clean openapi-postgen cov

openapi-gen: openapi-clean
	docker run --rm \
	  --user $(shell id -u):$(shell id -g) \
	  -v "$(PWD):/local" \
	  openapitools/openapi-generator-cli:$(OPENAPI_GENERATOR_VERSION) \
	  generate \
	  -i /local/$(OPENAPI_SPEC) \
	  -g python \
	  -o /local/ff_iii_luciferin/openapi \
	  --global-property=models,modelDocs=false,modelTests=false

	$(MAKE) openapi-postgen


openapi-clean:
	rm -rf ff_iii_luciferin/openapi/*

openapi-postgen:
	@echo "Post-processing OpenAPI output"

	# 1️⃣ ensure models is a proper package
	mkdir -p ff_iii_luciferin/openapi/openapi_client/models
	touch ff_iii_luciferin/openapi/openapi_client/models/__init__.py

	# 2️⃣ expose openapi_client as top-level import
	printf '%s\n' \
		'"""' \
		'OpenAPI generated client (vendor code).' \
		'' \
		'Compatibility shim: exposes this package as `openapi_client`.' \
		'DO NOT import from domain or business logic.' \
		'"""' \
		'import sys' \
		'import ff_iii_luciferin.openapi.openapi_client as _openapi_client' \
		'' \
		'sys.modules["openapi_client"] = _openapi_client' \
		> ff_iii_luciferin/openapi/__init__.py

cmt:
	uv run uv run pre-commit run --all-files
	uv run cz commit

ruff:
	uv run ruff check . --fix
	uv run ruff format .

ty:
	uv run ty check ff_iii_luciferin

cov:
	uv run pytest --cov=ff_iii_luciferin --cov-report=term-missing
