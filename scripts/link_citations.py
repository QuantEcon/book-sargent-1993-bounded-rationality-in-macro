#!/usr/bin/env python3
"""Link plain-text author-year references in the MyST chapters to references.bib.

The conversion left every citation as plain prose ("Hurwicz (1951)"), so the
198-entry bibliography was never reachable and never rendered. This script finds
those references and rewrites them as MyST citation roles.

Matching is self-validating: the cite keys are the authors' surnames
concatenated with the year ("MarcetSargent1989a"), so a candidate is accepted
only when the key it implies actually exists in references.bib. Anything that
does not resolve is reported rather than guessed at.

Rendering preserves the original prose. `{cite:t}` renders as "Surname (Year)",
so where the book writes a first name ("Lennart Ljung (1977)") we keep it as
literal text in front of the role and let the role supply the rest.

    uv run python scripts/link_citations.py           # report only
    uv run python scripts/link_citations.py --apply   # rewrite the chapters
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper"
BIB = PAPER / "references.bib"

# Surnames may carry diacritics (Müller, Métivier), so the name class has to
# reach past ASCII.
_NAME = r"[A-ZÀ-Þ][A-Za-zÀ-ÿ'’.-]*"

# Horizontal whitespace only. Using `\s` here lets a match run across a line
# break, which once swallowed a whole paragraph into the heading above it:
# "## A model of Bray\n\nMargaret Bray (1982)" matched end to end and collapsed
# to one line. Chapter paragraphs are unwrapped, so every real citation sits on
# a single line and nothing is lost by refusing to cross one.
_H = r"[^\S\n]"

# "Marcet and Sargent (1989a)", "Rust, Palmer, and Miller (1992)", "Sims (1980)"
CITE_RE = re.compile(
    rf"(?P<names>{_NAME}(?:(?:,)?{_H}+(?:and{_H}+|&{_H}+)?{_NAME})*)"
    rf"(?P<gap>{_H}+)"
    r"\((?P<year>\d{4}[a-z]?)\)"
)

# Cases no rule can derive.
OVERRIDES = {
    # The bibliography disambiguates with an initial the prose never supplies.
    ("Moore", "1993"): "MooreB1993",
    # ch05 fn92 cites "Evans and Honkapohja (1993)" with no letter, though the
    # book uses "(1993b)" elsewhere (ch05 fn81) -- the ambiguity is in the
    # original, not the conversion. Read as 1993b: the footnote describes
    # "path dependence", and 1993b is "Adaptive Forecasts, Hysteresis and
    # Endogenous Fluctuations", where hysteresis is that path dependence.
    # Worth confirming against the printed reference list.
    ("Honkapohja", "1993"): "EvansHonkapohja1993b",
}


def bib_keys() -> set[str]:
    return set(re.findall(r"^@\w+\{([^,]+),", BIB.read_text(encoding="utf-8"), re.M))


def _fold(s: str) -> str:
    """Strip diacritics: the bib is inconsistent (MullerReinhardt1990 folds the
    umlaut, BenvenisteMétivierPriouret1990 keeps the acute), so we try both."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _groups(names: str) -> list[list[str]]:
    """Split a name run into per-author groups on commas and 'and'."""
    parts = re.split(r",|\band\b|&", names)
    return [toks for p in parts if (toks := p.split())]


def _keyforms(surnames: list[str], year: str) -> list[str]:
    """Candidate keys, accent-preserved and accent-folded."""
    joined = "".join(surnames)
    out = []
    for variant in (joined, _fold(joined)):
        cleaned = re.sub(r"[^A-Za-zÀ-ÿ]", "", variant)
        out.append(cleaned + year)
    return out


def resolve(names: str, year: str, keys: set[str]) -> tuple[str | None, list[str], str]:
    """Return (key, leading_tokens_to_keep, style).

    The surname of each author is the last token of that author's group, so
    "See Sargent and Wallace" yields Sargent+Wallace with "See" left over as
    prose, and "Benveniste, Métivier, and Priouret" yields all three.

    `style` picks the role. Normally `{cite:t}`, which renders
    "Surname (Year)", with any leading first name kept as literal text in front
    ("Milton {cite:t}`FriedmanM1953`" -> "Milton Friedman (1953)").

    A possessive is the exception: "Muth's (1961)" would come out of `cite:t`
    as "Muth (1961)'s". There we keep the whole name phrase as prose and use
    `{cite:year}`, which renders just "(1961)", so the sentence still reads as
    printed and the reference is still linked.
    """
    groups = _groups(names)
    if not groups:
        return None, [], "t"

    surnames = [g[-1] for g in groups]
    prefix = groups[0][:-1]  # first names / "See" ahead of the first surname
    possessive = any(s.endswith(("'s", "’s")) for s in surnames)
    if possessive:
        surnames = [re.sub(r"['’]s$", "", s) for s in surnames]
    style = "year" if possessive else "t"

    candidates = list(_keyforms(surnames, year))
    # A single author may be disambiguated by first initial: FriedmanM1953.
    if len(surnames) == 1 and prefix:
        initial = _fold(prefix[-1])[:1].upper()
        candidates += [k[: -len(year)] + initial + year for k in _keyforms(surnames, year)]

    for key in candidates:
        if key in keys:
            return key, prefix, style
    # Only once the derivable forms are exhausted.
    if (key := OVERRIDES.get((surnames[-1], year))) and key in keys:
        return key, prefix, style
    return None, prefix, style


def scan(text: str, keys: set[str]) -> list[dict]:
    found = []
    for m in CITE_RE.finditer(text):
        names, year = m.group("names"), m.group("year")
        key, prefix, style = resolve(names, year, keys)
        found.append(
            {
                "span": m.span(),
                "raw": m.group(0),
                "names": names,
                "year": year,
                "key": key,
                "prefix": prefix,
                "style": style,
                "gap": m.group("gap"),
            }
        )
    return found


def rewrite(text: str, hits: list[dict]) -> tuple[str, int]:
    """Apply citations back-to-front so earlier spans stay valid."""
    n = 0
    for h in sorted(hits, key=lambda x: -x["span"][0]):
        if not h["key"]:
            continue
        start, end = h["span"]
        role = f"{{cite:{h['style']}}}`{h['key']}`"
        if h["style"] == "year":
            # Keep the full name phrase; the role supplies only "(year)".
            lead = h["names"]
        else:
            lead = " ".join(h["prefix"])
        text = text[:start] + (f"{lead}{h['gap']}{role}" if lead else role) + text[end:]
        n += 1
    return text, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes to disk")
    args = ap.parse_args()

    keys = bib_keys()
    print(f"references.bib: {len(keys)} entries\n")

    total, linked = 0, 0
    unresolved: Counter[str] = Counter()
    used: set[str] = set()

    already = 0
    for md in sorted(PAPER.glob("ch0*.md")):
        text = md.read_text(encoding="utf-8")
        hits = scan(text, keys)
        ok = [h for h in hits if h["key"]]
        total += len(hits)
        linked += len(ok)
        used.update(h["key"] for h in ok)
        for h in hits:
            if not h["key"]:
                unresolved[h["raw"].strip()] += 1

        # Roles already in the file, so a re-run still reports the true state
        # rather than "0 of 198 cited" once the rewrite has been applied.
        existing = re.findall(r"\{cite[^}]*\}`([^`]+)`", text)
        already += len(existing)
        used.update(existing)

        pending = f"{len(ok)}/{len(hits)} to link" if hits else "nothing to link"
        print(f"  {md.name:<10} {len(existing):>3} already linked, {pending}")

        if args.apply and ok:
            new_text, _ = rewrite(text, hits)
            md.write_text(new_text, encoding="utf-8")

    print(f"\nplain-text refs found: {total}, resolvable: {linked}")
    print(f"citation roles already present: {already}")
    print(f"distinct bib keys cited: {len(used & keys)} of {len(keys)} "
          f"({len(keys - used)} uncited)")

    if unresolved:
        print(f"\nno matching bib key ({sum(unresolved.values())} occurrences):\n")
        for raw, count in unresolved.most_common():
            print(f"  {count:>2}x  {raw}")

    print("\nchapters rewritten." if args.apply else "\n(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
