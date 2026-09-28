from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_release_notes(changelog: str, release_tag: str) -> str:
    """Return the body of the changelog section for ``release_tag``."""
    heading = re.compile(rf"^##\s+{re.escape(release_tag)}(?:\s+\([^)]*\))?\s*$")
    lines = changelog.splitlines()

    start = next(
        (index + 1 for index, line in enumerate(lines) if heading.fullmatch(line)), None
    )
    if start is None:
        raise ValueError(f"No changelog section found for {release_tag}")

    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    notes = "\n".join(lines[start:end]).strip()
    if not notes:
        raise ValueError(f"Changelog section for {release_tag} is empty")
    return f"{notes}\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract one release section from a Commitizen changelog."
    )
    parser.add_argument("release_tag", help="Release tag, for example v0.2.0")
    parser.add_argument("output", type=Path, help="Destination Markdown file")
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Changelog path (default: CHANGELOG.md)",
    )
    args = parser.parse_args()

    try:
        notes = extract_release_notes(
            args.changelog.read_text(encoding="utf-8"), args.release_tag
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    args.output.write_text(notes, encoding="utf-8")


if __name__ == "__main__":
    main()
