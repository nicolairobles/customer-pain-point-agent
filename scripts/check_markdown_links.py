"""Check internal markdown links in the repo.

This is a lightweight sanity check intended for CI/local runs. It validates:
- relative links to files exist
- relative links to headings exist (best-effort)

It does not validate external HTTP links.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _slugify_heading(text: str) -> str:
    # GitHub-ish slug rules (simplified).
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text


def _extract_heading_slugs(markdown: str) -> set[str]:
    slugs: set[str] = set()
    for line in markdown.splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip()
        if not heading:
            continue
        slugs.add(_slugify_heading(heading))
    return slugs


@dataclass
class LinkError:
    file: Path
    target: str
    reason: str


def _iter_markdown_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".md":
            yield path
        elif path.is_dir():
            yield from path.rglob("*.md")


def check_file(md_path: Path, repo_root: Path) -> list[LinkError]:
    errors: list[LinkError] = []
    content = md_path.read_text(encoding="utf-8", errors="replace")
    headings = _extract_heading_slugs(content)

    for _, raw_target in _MD_LINK_RE.findall(content):
        target = raw_target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            anchor = target[1:]
            if anchor and anchor not in headings:
                errors.append(LinkError(md_path, target, "missing in-page heading anchor"))
            continue

        path_part, _, anchor = target.partition("#")
        if path_part.startswith("/"):
            candidate = repo_root / path_part.lstrip("/")
        else:
            candidate = (md_path.parent / path_part).resolve()

        try:
            candidate.relative_to(repo_root.resolve())
        except Exception:
            # Outside repo; ignore.
            continue

        if not candidate.exists():
            errors.append(LinkError(md_path, target, f"missing file: {candidate}"))
            continue

        if anchor and candidate.suffix.lower() == ".md":
            other_headings = _extract_heading_slugs(candidate.read_text(encoding="utf-8", errors="replace"))
            if anchor not in other_headings:
                errors.append(LinkError(md_path, target, "missing heading anchor in target file"))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check internal markdown links.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["README.md", "docs"],
        help="Files/directories to scan (default: README.md docs/)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    scan_paths = [repo_root / p for p in args.paths]

    all_errors: list[LinkError] = []
    for md_path in _iter_markdown_files(scan_paths):
        all_errors.extend(check_file(md_path, repo_root))

    if all_errors:
        for err in all_errors:
            print(f"{err.file.relative_to(repo_root)}: {err.target} -> {err.reason}")
        print(f"\nFound {len(all_errors)} link issue(s).")
        return 1

    print("OK: no internal markdown link issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

