## v1.0.0a0 (2026-01-07)

### BREAKING CHANGE

- Fixes #6

### Refactor

- adjusted ci workflow
- adjust mypy scope and CI typecheck target
- rename project to ff-iii-luciferin
- **api**: Update client mapping contract and tests
- **api**: simplify Firefly client updates
- **api**: move firefly client to api layer and re-export helpers
- reo of files
- **openapi**: reo of model files
- added auto-generated firefly models
- **openapi**: add spec, generator makefile, and exclude generated api from tooling
- **examples**: add shared settings and logging; drop py3.11 CI
- migrate FireflyClient to async httpx client

## v0.7.0 (2025-11-16)

### Feat

- **fetch_categories**: added conditional start and end date parameters (for server side filtering)

## v0.6.1 (2025-08-04)

### Fix

- **filter_without_category**: fix

## v0.6.0 (2025-08-04)

### Feat

- **firefly_client**: added category assign

## v0.5.0 (2025-08-03)

### Feat

- **firefly_client**: fetch categories
- add category retrieval

## v0.4.9 (2025-08-02)

### Fix

- **typing**: changed pyproject.toml

## v0.4.8 (2025-07-29)

### Fix

- **SimplifiedTx**: notes added

## v0.4.7 (2025-07-29)

### Feat

- **filter_without_tag**: new function

### Fix

- **SimplifiedTx**: added notes field

### Refactor

- **var**: fixing mypy & pylint issues

## v0.4.6 (2025-07-21)

### Refactor

- black

## v0.4.5 (2025-07-21)

### Fix

- **pyproject**: desc
