#!/usr/bin/env python3
"""Structural assertions over the converted chapters. Exits non-zero on failure.

This is the half of the fidelity check that needs no source PDF, so unlike
`validate_prose.py` it can run in CI. The source scan is gitignored (it is a
copyrighted 8 MB book), which means prose coverage can only be measured by
someone holding a local copy — everything here works from the Markdown alone.

Each check is binary and has caught a real defect at least once:

  footnotes    every marker resolves to a definition and vice versa, labels run
               fn1..fnN with no gaps or duplicates. Restoring a dropped footnote
               once left a duplicate `fn61` behind.
  equations    each chapter's labels form a complete 1..max run. Five equations
               were printed in the book but carried no label, so nothing could
               cross-reference them, and one reference then pointed at the wrong
               equation.
  references   every {eq}, {numref} and {ref} target resolves to a defined label,
               and every cite key exists in the bibliography.
  figures      every referenced image is on disk. Two were referenced for months
               without existing.
  headings     no heading looks like it has swallowed body text. A citation
               rewrite once collapsed a paragraph into the heading above it, and
               prose-coverage scoring could not see it because every word was
               still present and still in order.

    uv run python scripts/check_structure.py
    uv run python scripts/check_structure.py --quiet   # only report failures
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper"
CHAPTERS = sorted(PAPER.glob("ch0*.md"))
BIB = PAPER / "references.bib"


class Report:
    def __init__(self, quiet: bool) -> None:
        self.failures: list[str] = []
        self.quiet = quiet

    def ok(self, check: str, detail: str) -> None:
        if not self.quiet:
            print(f"  PASS  {check:<12} {detail}")

    def fail(self, check: str, detail: str) -> None:
        print(f"  FAIL  {check:<12} {detail}")
        self.failures.append(f"{check}: {detail}")


def check_footnotes(rep: Report) -> None:
    numbers: list[int] = []
    bad = False
    for md in CHAPTERS:
        text = md.read_text(encoding="utf-8")
        defs = re.findall(r"^\[\^(fn[A-Za-z0-9]+)\]:", text, re.M)
        refs = re.findall(r"\[\^(fn[A-Za-z0-9]+)\](?!:)", text)
        dup_def = [k for k, v in Counter(defs).items() if v > 1]
        dup_ref = [k for k, v in Counter(refs).items() if v > 1]
        orphan_def = sorted(set(defs) - set(refs))
        orphan_ref = sorted(set(refs) - set(defs))
        if dup_def or dup_ref or orphan_def or orphan_ref:
            bad = True
            rep.fail(
                "footnotes",
                f"{md.name}: duplicate-def={dup_def} duplicate-ref={dup_ref} "
                f"def-without-marker={orphan_def} marker-without-def={orphan_ref}",
            )
        numbers += [int(d[2:]) for d in defs if d[2:].isdigit()]

    if numbers:
        gaps = [i for i in range(1, max(numbers) + 1) if i not in numbers]
        if gaps:
            bad = True
            rep.fail("footnotes", f"label sequence has gaps: {gaps}")
    if not bad:
        # Guard the empty case: with no numeric labels anywhere, max() would
        # raise and the run would die on a traceback instead of reporting.
        span = f", fn1..fn{max(numbers)}" if numbers else ""
        rep.ok("footnotes", f"{len(numbers)} footnotes{span}, all paired")


def check_equations(rep: Report) -> tuple[set[str], set[str]]:
    defined: set[str] = set()
    referenced: set[str] = set()
    bad = False
    for md in CHAPTERS:
        text = md.read_text(encoding="utf-8")
        labels = re.findall(r"\$\$\s*\((eq-\d+-\d+[a-z]?)\)", text)
        dup = [k for k, v in Counter(labels).items() if v > 1]
        if dup:
            bad = True
            rep.fail("equations", f"{md.name}: duplicate labels {dup}")
        defined |= set(labels)
        referenced |= set(re.findall(r"\{eq\}`([^`]+)`", text))

        nums = sorted({int(re.match(r"eq-\d+-(\d+)", l).group(1)) for l in labels})
        if nums:
            chapter = re.match(r"eq-(\d+)-", labels[0]).group(1)
            missing = [n for n in range(1, max(nums) + 1) if n not in nums]
            if missing:
                bad = True
                rep.fail(
                    "equations",
                    f"{md.name}: numbering gaps -> "
                    + ", ".join(f"{chapter}.{n}" for n in missing),
                )
    if not bad:
        rep.ok("equations", f"{len(defined)} labelled, every chapter runs 1..max")
    return defined, referenced


def check_references(rep: Report, eq_defined: set[str], eq_referenced: set[str]) -> None:
    dangling = sorted(eq_referenced - eq_defined)
    if dangling:
        rep.fail("references", f"{{eq}} targets with no definition: {dangling}")
    else:
        rep.ok("references", f"{len(eq_referenced)} {{eq}} refs all resolve")

    # {numref} and {ref} point at directive labels and section targets. These
    # are mostly figure references, so this is the check that guards against a
    # caption pointing somewhere that no longer exists.
    targets: set[str] = set()
    labelled: set[str] = set()
    for md in CHAPTERS:
        text = md.read_text(encoding="utf-8")
        targets |= set(re.findall(r"\{(?:numref|ref)\}`([^`]+)`", text))
        labelled |= set(re.findall(r"^:(?:label|name):\s*(\S+)", text, re.M))
        labelled |= set(re.findall(r"^\(([A-Za-z0-9_-]+)\)=", text, re.M))
    unresolved = sorted(targets - labelled)
    if unresolved:
        rep.fail("references", f"{{numref}}/{{ref}} targets with no label: {unresolved}")
    else:
        rep.ok("references", f"{len(targets)} {{numref}}/{{ref}} targets all resolve")

    keys = set(re.findall(r"^@\w+\{([^,]+),", BIB.read_text(encoding="utf-8"), re.M))
    used: set[str] = set()
    for md in CHAPTERS:
        used |= set(re.findall(r"\{cite[^}]*\}`([^`]+)`", md.read_text(encoding="utf-8")))
    unknown = sorted(used - keys)
    if unknown:
        rep.fail("references", f"cite keys not in references.bib: {unknown}")
    else:
        rep.ok("references", f"{len(used)} cite keys all present in the bibliography")


def check_figures(rep: Report) -> None:
    missing, total, labels = [], 0, []
    for md in CHAPTERS:
        text = md.read_text(encoding="utf-8")
        labels += re.findall(r"^:(?:label|name):\s*(fig-[\w-]+)", text, re.M)
        for img in re.findall(r"figures/[\w.-]+\.(?:jpeg|jpg|png|svg)", text):
            total += 1
            if not (PAPER / img).exists():
                missing.append(f"{md.name} -> {img}")
    dup = [k for k, v in Counter(labels).items() if v > 1]
    if missing:
        rep.fail("figures", f"referenced but not on disk: {missing}")
    if dup:
        rep.fail("figures", f"duplicate figure labels: {dup}")
    if not missing and not dup:
        rep.ok("figures", f"{total} references resolve, {len(labels)} labels unique")


def check_headings(rep: Report) -> None:
    suspects = []
    for md in CHAPTERS:
        for h in re.findall(r"^#{1,6}[^\S\n]+(.+)$", md.read_text(encoding="utf-8"), re.M):
            # The period must end a word, not a section number: "6. Experiments"
            # is a heading; "…equilibrium. These features" is swallowed prose.
            if len(h) > 90 or re.search(r"[a-z]\.\s+[A-Z]", h) or "{cite" in h:
                suspects.append(f"{md.name}: {h[:80]}")
    if suspects:
        rep.fail("headings", f"look like they absorbed body text: {suspects}")
    else:
        rep.ok("headings", "none look like they absorbed body text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    args = ap.parse_args()

    if not CHAPTERS:
        print("no chapter files found under paper/", file=sys.stderr)
        return 1

    rep = Report(args.quiet)
    if not args.quiet:
        print(f"\nStructural checks over {len(CHAPTERS)} chapters\n")

    check_footnotes(rep)
    eq_defined, eq_referenced = check_equations(rep)
    check_references(rep, eq_defined, eq_referenced)
    check_figures(rep)
    check_headings(rep)

    if rep.failures:
        print(f"\n{len(rep.failures)} check(s) failed.")
        return 1
    if not args.quiet:
        print("\nAll structural checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
