#!/usr/bin/env python3
"""Generate one class-specific MCT repository from the canonical template."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
DEFAULT_OUTPUT = ROOT / "dist"
COURSE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MCT_<CLASS> from the canonical MCT template."
    )
    parser.add_argument("course", help="Class/course key, e.g. I3A or E3A")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Parent directory for generated repositories (default: ./dist)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing generated repository directory",
    )
    return parser.parse_args()


def substitute_text_files(root: Path, values: dict[str, str]) -> None:
    """Replace explicit template markers in UTF-8 text files only."""
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        new_text = text
        for marker, replacement in values.items():
            new_text = new_text.replace(marker, replacement)

        if new_text != text:
            path.write_text(new_text, encoding="utf-8")


def find_unresolved_markers(root: Path) -> list[str]:
    unresolved: list[str] = []
    marker_re = re.compile(r"@[A-Z][A-Z0-9_]*@")

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in marker_re.finditer(text):
            unresolved.append(f"{path.relative_to(root)}: {match.group(0)}")

    return unresolved


def main() -> int:
    args = parse_args()
    course = args.course.strip()
    if not COURSE_RE.fullmatch(course):
        raise SystemExit(
            "ERROR: course must match [A-Za-z0-9][A-Za-z0-9._-]* "
            "(examples: I3A, E3A)."
        )

    repo_name = f"MCT_{course}"
    output_root = args.output_dir.expanduser().resolve()
    destination = output_root / repo_name

    if destination.exists():
        if not args.force:
            raise SystemExit(
                f"ERROR: destination already exists: {destination}\n"
                "       Re-run with --force to replace it."
            )
        shutil.rmtree(destination)

    output_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, destination, copy_function=shutil.copy2)

    substitute_text_files(
        destination,
        {
            "@CLASS@": course,
            "@REPO_NAME@": repo_name,
        },
    )

    unresolved = find_unresolved_markers(destination)
    if unresolved:
        shutil.rmtree(destination)
        details = "\n".join(f"  {item}" for item in unresolved)
        raise SystemExit(
            "ERROR: unresolved template marker(s); generated tree removed:\n"
            f"{details}"
        )

    print(f"Generated {repo_name}: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
