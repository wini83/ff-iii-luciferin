.PHONY: openapi-gen openapi-clean openapi-postgen

openapi-gen: openapi-clean
	docker run --rm \
	  --user $(shell id -u):$(shell id -g) \
	  -v "$(PWD):/local" \
	  openapitools/openapi-generator-cli:latest \
	  generate \
	  -i /local/openapi/firefly-iii-6.4.14-v1.yaml \
	  -g python-pydantic-v1 \
	  -o /local/fireflyiii_enricher_core/openapi \
	  --global-property=models,modelDocs=false,modelTests=false

	$(MAKE) openapi-postgen


openapi-clean:
	rm -rf fireflyiii_enricher_core/openapi/*

openapi-postgen:
	@echo "Post-processing OpenAPI output"

	# 1️⃣ ensure models is a proper package
	mkdir -p fireflyiii_enricher_core/openapi/openapi_client/models
	touch fireflyiii_enricher_core/openapi/openapi_client/models/__init__.py

	# 2️⃣ expose openapi_client as top-level import
	printf '%s\n' \
		'"""' \
		'OpenAPI generated client (vendor code).' \
		'' \
		'Compatibility shim: exposes this package as `openapi_client`.' \
		'DO NOT import from domain or business logic.' \
		'"""' \
		'import sys' \
		'import fireflyiii_enricher_core.openapi.openapi_client as _openapi_client' \
		'' \
		'sys.modules["openapi_client"] = _openapi_client' \
		> fireflyiii_enricher_core/openapi/__init__.py
