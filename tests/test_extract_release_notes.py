from __future__ import annotations

import pytest

from scripts.extract_release_notes import extract_release_notes

CHANGELOG = """\
## Unreleased

## v0.3.0 (2026-09-20)

### Feat

- add release automation

## v0.3.0rc1 (2026-09-19)

### Fix

- stabilize release automation

## v0.2.0 (2026-09-18)

### Feat

- expose component upsert result
"""


def test_extract_release_notes_returns_only_requested_section() -> None:
    assert extract_release_notes(CHANGELOG, "v0.3.0") == (
        "### Feat\n\n- add release automation\n"
    )


def test_extract_release_notes_does_not_confuse_prerelease_prefix() -> None:
    assert extract_release_notes(CHANGELOG, "v0.3.0rc1") == (
        "### Fix\n\n- stabilize release automation\n"
    )


def test_extract_release_notes_rejects_missing_version() -> None:
    with pytest.raises(ValueError, match="No changelog section found for v9.9.9"):
        extract_release_notes(CHANGELOG, "v9.9.9")


def test_extract_release_notes_rejects_empty_section() -> None:
    with pytest.raises(ValueError, match="Changelog section for v1.0.0 is empty"):
        extract_release_notes("## v1.0.0 (2026-09-20)\n", "v1.0.0")
