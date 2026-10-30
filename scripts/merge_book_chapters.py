#!/usr/bin/env python3
"""Merge book chapters into a single Markdown file (full manuscript or audiobook transcript)."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

INLINE_FOOTNOTE_RE = re.compile(r"\[\^[^^\]]+\]")
NOTES_HEADING_RE = re.compile(r"^## (?:Notes|Sources|Further Reading|Linked evidence cards)\s*$", re.MULTILINE)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_book_path(root: Path, book_arg: Path) -> Path:
    """Resolve a book or series path whether passed relative to root or by short folder name."""
    direct = book_arg.resolve() if book_arg.is_absolute() else (root / book_arg).resolve()
    if direct.is_dir():
        return direct
    for candidate in (
        root / "series" / "architectures-of-memory" / book_arg.name,
        root / "series" / book_arg.name,
    ):
        if candidate.is_dir():
            return candidate.resolve()
    return direct


def iter_chapter_files(chapters_dir: Path) -> list[Path]:
    """Return sorted chapter markdown files, excluding _OUTLINE.md, _TEMPLATE.md, and index.md."""
    if not chapters_dir.is_dir():
        return []
    return [
        p
        for p in sorted(chapters_dir.glob("*.md"))
        if not p.name.startswith("_") and p.name.lower() not in ("index.md", "readme.md")
    ]


def strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\r\n")
    return text


def transform_audiobook(text: str) -> str:
    stripped = strip_yaml_frontmatter(text)
    lines: list[str] = []
    for line in stripped.splitlines(keepends=True):
        if line.lstrip().startswith("*Sources:") or line.lstrip().startswith("> **Domain"):
            continue
        lines.append(line)
    body = "".join(lines)
    m = NOTES_HEADING_RE.search(body)
    if m:
        body = body[: m.start()]
    body = INLINE_FOOTNOTE_RE.sub("", body)
    return body.rstrip()


def preamble_full(book_rel: str) -> str:
    today = date.today().isoformat()
    return f"""# {book_rel} — Full manuscript

Compiled from `{book_rel}/chapters/*.md` in sorted filename order ({today}).

**Footnotes:** Each chapter defines reference-style footnotes locally. Some labels repeat across chapters; in one file, renderers may attach one definition to every use of a label.

---

"""


def preamble_audiobook(book_rel: str) -> str:
    today = date.today().isoformat()
    return f"""# {book_rel} — Audiobook transcript

Compiled from `{book_rel}/chapters/*.md` ({today}). YAML frontmatter, *Sources* lines, `## Notes` / `## Sources` sections, and inline `[^footnote]` markers are omitted for text-to-speech.

---

"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge chapters/*.md under a book or series directory into one file.",
    )
    parser.add_argument(
        "book",
        type=Path,
        help="Book directory relative to repo root or short name (e.g. series/architectures-of-memory/book-01-vanishing-signal or series/parenthood-atlas).",
    )
    parser.add_argument(
        "--audiobook",
        action="store_true",
        help="Strip YAML frontmatter, Sources, Notes, and inline footnote calls (TTS-friendly).",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        metavar="NAME",
        help="Output basename (default: book folder name). E.g. --prefix vanishing-signal",
    )
    args = parser.parse_args()

    root = repo_root()
    book_path = resolve_book_path(root, args.book)

    if not book_path.is_dir():
        print(f"error: not a directory: {book_path}", file=sys.stderr)
        sys.exit(1)

    chapters_dir = book_path / "chapters"
    if not chapters_dir.is_dir():
        print(f"error: missing chapters/: {chapters_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = iter_chapter_files(chapters_dir)
    if not md_files:
        print(f"error: no chapter *.md under {chapters_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        book_rel = book_path.relative_to(root).as_posix()
    except ValueError:
        book_rel = book_path.name

    base_name = book_path.parent.parent.name if book_path.parent.name == "i18n" else book_path.name
    prefix = args.prefix or base_name
    suffix = "audiobook" if args.audiobook else "full"
    out_name = f"{prefix}-{suffix}.md"
    out_path = book_path / out_name

    sep = "\n\n---\n\n"
    preamble = preamble_audiobook(book_rel) if args.audiobook else preamble_full(book_rel)
    parts: list[str] = [preamble.rstrip("\n") + "\n\n"]

    front_matter_file = book_path / "front-matter.md"
    if front_matter_file.is_file():
        fm_raw = front_matter_file.read_text(encoding="utf-8")
        fm_body = transform_audiobook(fm_raw) if args.audiobook else strip_yaml_frontmatter(fm_raw).rstrip()
        parts.append(fm_body)
        parts.append(sep)

    for i, f in enumerate(md_files):
        raw = f.read_text(encoding="utf-8")
        body = transform_audiobook(raw) if args.audiobook else strip_yaml_frontmatter(raw).rstrip()
        parts.append(body)
        if i < len(md_files) - 1:
            parts.append(sep)

    out_path.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out_path} ({len(md_files)} chapters)")


if __name__ == "__main__":
    main()
