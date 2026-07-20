#!/usr/bin/env python3
"""Prose-fidelity validation: source PDF text layer vs converted MyST chapters.

The source PDF is a scan carrying an OCR text layer, which gives us an
independent channel to check the conversion against -- independent in the sense
that it does not pass through marker-pdf, so content marker dropped is still
visible here.

Method: n-gram coverage rather than a sequential diff. For each chapter we
tokenise both sides to bare words and ask what fraction of the PDF's n-grams
appear anywhere in the MyST chapter. This is order-insensitive, so footnotes
migrating from page-bottom (PDF) to inline definitions (MyST) do not register as
loss. Runs of consecutive uncovered n-grams are reported as candidate dropped
passages.

Caveats, which matter when reading the output:
  - The OCR layer garbles displayed equations, so uncovered runs cluster around
    maths. Those are OCR noise, not conversion loss.
  - The OCR layer does not capture equation numbers at all, so equation
    numbering cannot be validated here -- that needs visual comparison.
  - Figures are images; nothing to compare textually.

Usage:
    uv run python scripts/validate_prose.py
    uv run python scripts/validate_prose.py --n 8 --min-run 20
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper"
SOURCE_PDF = next((ROOT / "source").glob("*.pdf"), None)

# Chapter -> (number, title). A chapter's opening page carries the bare number
# on one line and the title on the next, with no running header -- that is how
# we find chapter boundaries. Verso pages carry "N  Chapter M: Title" and recto
# pages carry the current section title, so headers alone cannot delimit
# chapters.
CHAPTERS = {
    "ch01": (1, "Introduction"),
    "ch02": (2, "Expectations and Behavior"),
    "ch03": (3, "Data Structures"),
    "ch04": (4, "Networks and Artificial Intelligence"),
    "ch05": (5, "Adaptation in Artificial Economies"),
    "ch06": (6, "Experiments"),
    "ch07": (7, "Applications"),
}

# Running header on verso pages, stripped before comparison.
CHAPTER_HEADERS = {
    c: f"Chapter {n}: {t}" for c, (n, t) in CHAPTERS.items()
}


def pdf_pages() -> list[str]:
    """Return the PDF text layer split into pages."""
    if SOURCE_PDF is None:
        sys.exit("No PDF found under source/")
    out = subprocess.run(
        ["pdftotext", str(SOURCE_PDF), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.split("\f")


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def find_chapter_starts(pages: list[str]) -> dict[str, int]:
    """Locate the opening page of each chapter.

    An opening page begins with the chapter number followed by the chapter
    title. Matching on that pattern -- rather than forward-filling running
    headers -- is what keeps a chapter's first pages from being attributed to
    the previous chapter.

    The numeral is set as a large display glyph, which the OCR often mangles
    ("1" -> "|", "4" -> "+"), so we match on a short leading token followed by
    the exact chapter title. Requiring the title to sit on its own line
    distinguishes an opening page from a recto running header carrying a
    same-named section title, and from the table of contents (which lists
    several chapter titles on one page).
    """
    starts: dict[str, int] = {}
    for idx, page in enumerate(pages):
        lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
        if len(lines) < 3 or len(page) < 400:
            continue
        # A table of contents lists several chapter titles each on its own
        # line. Prose merely mentioning a title ("the following chapter on
        # neural networks and artificial intelligence") must not count, so we
        # only look at lines that consist of a title and nothing else.
        standalone = {_norm(ln) for ln in lines}
        if sum(1 for _, t in CHAPTERS.values() if _norm(t) in standalone) > 1:
            continue
        for chapter, (_num, title) in CHAPTERS.items():
            if chapter in starts:
                continue
            if len(lines[0]) <= 3 and _norm(lines[1]) == _norm(title):
                starts[chapter] = idx
    missing = set(CHAPTERS) - set(starts)
    if missing:
        sys.exit(f"Could not locate opening page for: {sorted(missing)}")
    return starts


def find_back_matter(pages: list[str], after: int) -> int:
    """First page of the back matter, which bounds the final chapter."""
    for idx in range(after, len(pages)):
        lines = [ln.strip() for ln in pages[idx].splitlines() if ln.strip()]
        if lines and _norm(lines[0]) == "references":
            return idx
    return len(pages)


def attribute_pages(pages: list[str]) -> dict[str, list[str]]:
    """Map each chapter to its contiguous page range."""
    starts = find_chapter_starts(pages)
    order = sorted(starts, key=lambda c: starts[c])
    bounds: dict[str, tuple[int, int]] = {}
    for i, chapter in enumerate(order):
        begin = starts[chapter]
        if i + 1 < len(order):
            end = starts[order[i + 1]]
        else:
            end = find_back_matter(pages, begin)
        bounds[chapter] = (begin, end)
    return {c: pages[a:b] for c, (a, b) in bounds.items()}


def clean_pdf_text(pages: list[str], section_headings: set[str]) -> str:
    """Strip page furniture: page numbers, chapter headers, section headers.

    Recto pages carry the current section title as a running header. Left in,
    each one produces an n-gram spanning header into body text that can never
    match, depressing coverage for no real reason. We drop a leading short line
    only when it matches a heading actually present in the MyST chapter, so
    body prose is never removed.
    """
    cleaned = []
    for page in pages:
        lines = [ln for ln in page.splitlines()]
        keep = []
        seen_body = False
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.fullmatch(r"\d{1,3}", s):  # bare page number
                continue
            if any(m in s for m in CHAPTER_HEADERS.values()):
                continue
            # Running section header: only near the top, only if it is a real
            # heading from the chapter.
            if not seen_body and len(s) < 60 and _norm(s) in section_headings:
                continue
            seen_body = True
            keep.append(line)
        cleaned.append("\n".join(keep))
    return "\n".join(cleaned)


def myst_headings(md: str) -> set[str]:
    """Normalised heading text from a MyST chapter, for header stripping."""
    return {_norm(m) for m in re.findall(r"^#{1,6}\s+(.+)$", md, flags=re.M)}


def looks_like_maths(text: str) -> bool:
    """Heuristic: is an uncovered run OCR'd maths rather than dropped prose?

    Garbled equation OCR is dominated by very short tokens and digits
    ("ry c2t zt 1 pt of b ro r141"), whereas real prose has ordinary word
    lengths and few bare numerals.
    """
    toks = text.split()
    if not toks:
        return False
    short = sum(1 for t in toks if len(t) <= 2)
    digits = sum(1 for t in toks if any(ch.isdigit() for ch in t))
    return (short + digits) / len(toks) > 0.45


def _surnames(key: str) -> str:
    """Recover author surnames from a cite key ("MarcetSargent1989a")."""
    stem = re.sub(r"\d{4}[a-z]?$", "", key)
    return " " + " ".join(re.findall(r"[A-ZÀ-Þ][a-zà-ÿ]*", stem)) + " "


def clean_myst_text(md: str) -> str:
    """Reduce a MyST chapter to its prose."""
    # YAML frontmatter
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    # Display maths (OCR cannot match these anyway)
    md = re.sub(r"\$\$.*?\$\$\s*(\(eq-[^)]+\))?", " ", md, flags=re.S)
    # Directive fences and their options
    md = re.sub(r"^:::+\{[^}]*\}.*$", " ", md, flags=re.M)
    md = re.sub(r"^:::+\s*$", " ", md, flags=re.M)
    md = re.sub(r"^```.*$", " ", md, flags=re.M)
    md = re.sub(r"^:(label|name|width|align|alt):.*$", " ", md, flags=re.M)
    # Section target labels
    md = re.sub(r"^\([a-z0-9-]+\)=\s*$", " ", md, flags=re.M)
    # Citation roles stand in for author names that the PDF still prints, so
    # expand them back rather than deleting them -- otherwise linking a
    # citation would look like prose going missing. `cite:year` renders only
    # "(1994)" and leaves the names in the surrounding prose, so it expands to
    # nothing.
    md = re.sub(r"\{cite:year\}`[^`]*`", " ", md)
    md = re.sub(r"\{cite(?::[tp])?\}`([^`]*)`", lambda m: _surnames(m.group(1)), md)
    # Remaining roles are markup, not prose
    md = re.sub(r"\{(eq|numref|ref)\}`[^`]*`", " ", md)
    # Inline maths
    md = re.sub(r"\$[^$\n]*\$", " ", md)
    # Images / links
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    # Footnote markers (definitions keep their text, which is correct --
    # the PDF carries that text too)
    md = re.sub(r"\[\^fn\d+\]:", " ", md)
    md = re.sub(r"\[\^fn\d+\]", " ", md)
    return md


_WORD = re.compile(r"[a-z0-9]+")
_CONTENT_WORD = re.compile(r"[a-z]{4,}")


def tokenize(text: str, content_words: bool = True) -> list[str]:
    """Reduce text to comparable tokens.

    By default we keep only alphabetic tokens of four characters or more.
    Displayed and inline maths survives OCR as a stream of short, digit-laden
    fragments ("ry c2t zt 1 pt of b ro r141"); left in, a single garbled symbol
    breaks the n-gram chain through prose that converted perfectly well, so the
    score ends up tracking maths density rather than fidelity. Filtering to
    content words removes that noise from both sides. A genuinely dropped
    passage still shows up, because its content words go missing too.
    """
    text = text.lower()
    # Join words hyphenated across a line break
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    # Normalise the OCR's curly quotes and dashes away
    text = re.sub(r"[‘’“”–—]", " ", text)
    pattern = _CONTENT_WORD if content_words else _WORD
    return pattern.findall(text)


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def analyse(
    chapter: str,
    pdf_text: str,
    myst_text: str,
    n: int,
    min_run: int,
    content_words: bool = True,
) -> dict:
    pdf_tokens = tokenize(pdf_text, content_words)
    myst_tokens = tokenize(myst_text, content_words)

    pdf_grams = ngrams(pdf_tokens, n)
    myst_gram_set = set(ngrams(myst_tokens, n))

    covered = [g in myst_gram_set for g in pdf_grams]
    coverage = sum(covered) / len(covered) if covered else 0.0

    # Reverse direction: MyST content with no counterpart in the PDF.
    pdf_gram_set = set(pdf_grams)
    myst_grams = ngrams(myst_tokens, n)
    rev_covered = [g in pdf_gram_set for g in myst_grams]
    rev_coverage = sum(rev_covered) / len(rev_covered) if rev_covered else 0.0

    # Consecutive uncovered runs -> candidate dropped passages.
    runs = []
    start = None
    for i, ok in enumerate(covered):
        if not ok and start is None:
            start = i
        elif ok and start is not None:
            if i - start >= min_run:
                runs.append((start, i))
            start = None
    if start is not None and len(covered) - start >= min_run:
        runs.append((start, len(covered)))

    gaps = []
    for s, e in runs:
        snippet = " ".join(pdf_tokens[s : min(s + 40, e + n)])
        gaps.append(
            {
                "start_token": s,
                "length": e - s,
                "text": snippet,
                "kind": "maths" if looks_like_maths(snippet) else "prose",
            }
        )
    gaps.sort(key=lambda g: -g["length"])
    prose_gaps = [g for g in gaps if g["kind"] == "prose"]

    return {
        "chapter": chapter,
        "pdf_words": len(pdf_tokens),
        "myst_words": len(myst_tokens),
        "coverage": coverage,
        "reverse_coverage": rev_coverage,
        "gap_count": len(gaps),
        "prose_gap_count": len(prose_gaps),
        "maths_gap_count": len(gaps) - len(prose_gaps),
        "gaps": gaps,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="n-gram size")
    ap.add_argument(
        "--min-run", type=int, default=20, help="min consecutive uncovered n-grams to report"
    )
    ap.add_argument("--json", type=Path, help="also write results as JSON")
    ap.add_argument("--top", type=int, default=5, help="gaps to show per chapter")
    ap.add_argument(
        "--raw-tokens",
        action="store_true",
        help="compare every token including maths fragments (noisy; see tokenize)",
    )
    args = ap.parse_args()
    content_words = not args.raw_tokens

    pages = pdf_pages()
    by_chapter = attribute_pages(pages)

    results = []
    for chapter in sorted(CHAPTER_HEADERS):
        md_path = PAPER / f"{chapter}.md"
        if not md_path.exists():
            print(f"  skip {chapter}: no {md_path.name}")
            continue
        md = md_path.read_text(encoding="utf-8")
        pdf_text = clean_pdf_text(by_chapter[chapter], myst_headings(md))
        myst_text = clean_myst_text(md)
        results.append(
            analyse(chapter, pdf_text, myst_text, args.n, args.min_run, content_words)
        )

    mode = "raw tokens" if args.raw_tokens else "content words"
    print(f"\nProse fidelity — {args.n}-gram coverage ({mode}), PDF text layer vs MyST\n")
    print(
        f"{'chapter':<9}{'pdf words':>11}{'myst words':>12}"
        f"{'coverage':>11}{'reverse':>10}{'prose gaps':>12}{'maths gaps':>12}"
    )
    print("-" * 77)
    for r in results:
        print(
            f"{r['chapter']:<9}{r['pdf_words']:>11,}{r['myst_words']:>12,}"
            f"{r['coverage']:>10.1%}{r['reverse_coverage']:>10.1%}"
            f"{r['prose_gap_count']:>12}{r['maths_gap_count']:>12}"
        )

    tot_pdf = sum(r["pdf_words"] for r in results)
    tot_myst = sum(r["myst_words"] for r in results)
    weighted = (
        sum(r["coverage"] * r["pdf_words"] for r in results) / tot_pdf if tot_pdf else 0.0
    )
    tot_prose = sum(r["prose_gap_count"] for r in results)
    tot_maths = sum(r["maths_gap_count"] for r in results)
    print("-" * 77)
    print(
        f"{'TOTAL':<9}{tot_pdf:>11,}{tot_myst:>12,}{weighted:>10.1%}"
        f"{'':>10}{tot_prose:>12}{tot_maths:>12}"
    )

    print(f"\nProse gaps needing review (runs of >= {args.min_run} uncovered n-grams,")
    print("excluding runs classified as garbled equation OCR):\n")
    any_prose = False
    for r in results:
        pg = [g for g in r["gaps"] if g["kind"] == "prose"]
        if not pg:
            continue
        any_prose = True
        print(f"  {r['chapter']}:")
        for g in pg[: args.top]:
            print(f"    [{g['length']:>4} n-grams] {g['text'][:160]}…")
        print()
    if not any_prose:
        print("  none\n")

    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"JSON written to {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
