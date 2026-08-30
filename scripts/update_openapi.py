#!/usr/bin/env python3
"""Download the newest stable Firefly III OpenAPI v1 specification."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import cast

API_DOCS_CONTENTS_URL = (
    "https://api.github.com/repos/firefly-iii/api-docs/contents/dist?ref=main"
)
SPEC_PATTERN = re.compile(r"^firefly-iii-v?(\d+)\.(\d+)\.(\d+)-v1\.yaml$")
OPENAPI_DIR = Path("openapi")


def version_from_name(name: str) -> tuple[int, int, int] | None:
    match = SPEC_PATTERN.fullmatch(name)
    if match is None:
        return None
    major, minor, patch = map(int, match.groups())
    return major, minor, patch


def request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ff-iii-luciferin-openapi-updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def newest_upstream_spec() -> tuple[tuple[int, int, int], str, str]:
    with urllib.request.urlopen(request(API_DOCS_CONTENTS_URL), timeout=30) as response:
        entries = cast(list[dict[str, object]], json.load(response))

    candidates: list[tuple[tuple[int, int, int], str, str]] = []
    for entry in entries:
        name = entry.get("name")
        download_url = entry.get("download_url")
        if not isinstance(name, str) or not isinstance(download_url, str):
            continue
        version = version_from_name(name)
        if version is not None:
            candidates.append((version, name, download_url))

    if not candidates:
        raise RuntimeError("No stable Firefly III OpenAPI v1 specification found")
    return max(candidates)


def current_local_version() -> tuple[int, int, int] | None:
    versions = [
        version
        for path in OPENAPI_DIR.glob("firefly-iii-*-v1.yaml")
        if (version := version_from_name(path.name)) is not None
    ]
    return max(versions, default=None)


def set_output(name: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with Path(output_file).open("a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")
    sys.stdout.write(f"{name}={value}\n")


def download_spec(url: str, destination: Path) -> None:
    with urllib.request.urlopen(request(url), timeout=60) as response:
        content = response.read()
    if not content.startswith((b"openapi:", b"swagger:")):
        raise RuntimeError("Downloaded file does not look like an OpenAPI specification")

    OPENAPI_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=OPENAPI_DIR, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)


def main() -> int:
    upstream_version, upstream_name, download_url = newest_upstream_spec()
    local_version = current_local_version()
    version_text = ".".join(map(str, upstream_version))

    if local_version is not None and upstream_version <= local_version:
        set_output("changed", "false")
        set_output("version", version_text)
        return 0

    destination = OPENAPI_DIR / upstream_name
    download_spec(download_url, destination)
    for path in OPENAPI_DIR.glob("firefly-iii-*-v1.yaml"):
        if path != destination and version_from_name(path.name) is not None:
            path.unlink()

    set_output("changed", "true")
    set_output("version", version_text)
    set_output("spec", str(destination))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        sys.stderr.write(f"OpenAPI update failed: {error}\n")
        raise SystemExit(1) from error
