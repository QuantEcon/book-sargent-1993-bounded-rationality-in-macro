#!/usr/bin/env python3
"""Renumber footnote labels sequentially across the chapters, in document order.

The conversion convention is `[^fn1]` .. `[^fnN]` running across the whole book.
Restoring a dropped footnote breaks that, since a new note has to be inserted
mid-sequence under a temporary label (`fn59a`). This walks the chapters in TOC
order, reads each file's markers in the order they appear, and rewrites every
label to a fresh sequential number.

Labels are only identifiers -- MyST numbers footnotes at render time from
document order -- so this is cosmetic. It keeps the source readable and matching
the documented convention.

    uv run python scripts/renumber_footnotes.py           # report
    uv run python scripts/renumber_footnotes.py --apply   # rewrite
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper"
CHAPTERS = [f"ch{n:02d}.md" for n in range(1, 8)]

REF_RE = re.compile(r"\[\^(fn[A-Za-z0-9]+)\](?!:)")
DEF_RE = re.compile(r"^\[\^(fn[A-Za-z0-9]+)\]:", re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    texts = {c: (PAPER / c).read_text(encoding="utf-8") for c in CHAPTERS}

    # Integrity first: a rename is only safe if every marker pairs with a
    # definition inside the same file.
    problems = []
    for c, t in texts.items():
        refs, defs = REF_RE.findall(t), DEF_RE.findall(t)
        if len(refs) != len(set(refs)):
            problems.append(f"{c}: duplicate markers")
        if set(refs) != set(defs):
            problems.append(
                f"{c}: markers/definitions disagree "
                f"(+{sorted(set(refs)-set(defs))} -{sorted(set(defs)-set(refs))})"
            )
    if problems:
        print("refusing to renumber:")
        for p in problems:
            print("  " + p)
        return 1

    counter, renames = 0, {}
    for c in CHAPTERS:
        # Marker order in the body is the document order MyST will render.
        for old in REF_RE.findall(texts[c]):
            counter += 1
            renames[(c, old)] = f"fn{counter}"

    changed = sum(1 for (_, old), new in renames.items() if old != new)
    print(f"{counter} footnotes across {len(CHAPTERS)} chapters; "
          f"{changed} label(s) change")
    for (c, old), new in renames.items():
        if old != new:
            print(f"  {c}: {old} -> {new}")

    if not args.apply:
        print("\n(dry run -- pass --apply to write)")
        return 0

    for c in CHAPTERS:
        t = texts[c]
        # Two passes via a placeholder, so a rename never collides with a label
        # that has not been rewritten yet (fn61 -> fn62 while fn62 still exists).
        for old, new in ((o, n) for (cc, o), n in renames.items() if cc == c):
            t = t.replace(f"[^{old}]", f"[\x00{new}]")
        t = t.replace("[\x00", "[^")
        (PAPER / c).write_text(t, encoding="utf-8")
    print("\nrewritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
