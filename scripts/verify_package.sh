#!/usr/bin/env bash
set -euo pipefail

uv build --clear --quiet
uv run twine check --strict dist/*

package_env="$(mktemp -d)"
trap 'rm -rf "$package_env"' EXIT
uv venv --python 3.12 "$package_env"
uv pip install --python "$package_env/bin/python" dist/*.whl
(
  cd "$package_env"
  "$package_env/bin/python" -c 'from ff_iii_luciferin.api import FireflyClient; assert FireflyClient.__name__ == "FireflyClient"'
)
