.PHONY: openapi-gen openapi-clean

openapi-gen: openapi-clean
	docker run --rm \
	  --user $(shell id -u):$(shell id -g) \
	  -v "$(PWD):/local" \
	  openapitools/openapi-generator-cli:latest \
	  generate \
	  -i /local/openapi/firefly-iii-6.4.14-v1.yaml \
	  -g python-pydantic-v1 \
	  -o /local/fireflyiii_enricher_core/api \
	  --global-property=models,modelDocs=false,modelTests=false

openapi-clean:
	rm -rf fireflyiii_enricher_core/api/*
