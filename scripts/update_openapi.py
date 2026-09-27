#!/usr/bin/env python3
"""Download the newest stable Firefly III OpenAPI v1 specification."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast

RELEASES_URL = "https://api.github.com/repos/firefly-iii/firefly-iii/releases?per_page=100"
API_DOCS_RAW_URL = "https://raw.githubusercontent.com/firefly-iii/api-docs"
RELEASE_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
SPEC_PATTERN = re.compile(r"^firefly-iii-v?(\d+)\.(\d+)\.(\d+)-v1\.yaml$")
OPENAPI_DIR = Path("openapi")
BUGGY_BUDGET_CHART_VERSION = (6, 7, 4)


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


def stable_releases() -> list[tuple[tuple[int, int, int], str]]:
    with urllib.request.urlopen(request(RELEASES_URL), timeout=30) as response:
        entries = cast(list[dict[str, object]], json.load(response))

    releases: list[tuple[tuple[int, int, int], str]] = []
    for entry in entries:
        tag = entry.get("tag_name")
        if entry.get("draft") or entry.get("prerelease") or not isinstance(tag, str):
            continue
        match = RELEASE_PATTERN.fullmatch(tag)
        if match is not None:
            major, minor, patch = map(int, match.groups())
            releases.append(((major, minor, patch), tag))
    if not releases:
        raise RuntimeError("No stable Firefly III releases found")
    return sorted(releases, reverse=True)


def newest_published_spec(
    local_version: tuple[int, int, int] | None,
) -> tuple[tuple[int, int, int], str, bytes] | None:
    for version, tag in stable_releases():
        if local_version is not None and version <= local_version:
            break
        version_text = ".".join(map(str, version))
        # Older branches used filenames without the leading 'v'.
        names = [f"firefly-iii-{tag}-v1.yaml"]
        if tag.startswith("v"):
            names.append(f"firefly-iii-{version_text}-v1.yaml")
        for name in names:
            url = f"{API_DOCS_RAW_URL}/{tag}/dist/{name}"
            try:
                with urllib.request.urlopen(request(url), timeout=60) as response:
                    content = response.read()
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    # The release may precede publication of its documentation.
                    continue
                raise
            if not content.startswith((b"openapi:", b"swagger:")):
                raise RuntimeError(f"Downloaded {name} is not an OpenAPI specification")
            return version, name, content
        sys.stdout.write(f"OpenAPI specification for {tag} not published yet\n")
    return None


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


def save_spec(content: bytes, destination: Path) -> None:
    OPENAPI_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=OPENAPI_DIR, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)


def patch_known_upstream_issues(
    version: tuple[int, int, int], content: bytes
) -> bytes:
    if version != BUGGY_BUDGET_CHART_VERSION:
        return content

    # Firefly III 6.7.4 assigns getChartBudgetOverview to two chart endpoints.
    # Give the newer endpoint its own operationId without disabling validation.
    path = b"  /v1/chart/budget/overview-with-limits:\n"
    old_id = b"      operationId: getChartBudgetOverview\n"
    new_id = b"      operationId: getChartBudgetOverviewWithLimits\n"
    start = content.find(path)
    if start < 0:
        raise RuntimeError("Expected budget chart endpoint missing from 6.7.4 spec")
    end = content.find(b"\n  /v1/", start + len(path))
    if end < 0:
        end = len(content)
    section = content[start:end]
    if section.count(old_id) == 0 and content.count(old_id) == 1:
        return content  # Upstream has already corrected the duplicate.
    if section.count(old_id) != 1 or content.count(old_id) != 2:
        raise RuntimeError("Unexpected budget chart operationIds in 6.7.4 spec")
    return content[:start] + section.replace(old_id, new_id, 1) + content[end:]


def main() -> int:
    local_version = current_local_version()
    upstream = newest_published_spec(local_version)
    if upstream is None:
        set_output("changed", "false")
        return 0
    upstream_version, upstream_name, content = upstream
    version_text = ".".join(map(str, upstream_version))
    destination = OPENAPI_DIR / upstream_name
    save_spec(patch_known_upstream_issues(upstream_version, content), destination)
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
