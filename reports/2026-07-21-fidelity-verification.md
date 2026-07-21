# Verification Report: Independent Re-check of the Fidelity Report

**Date**: 2026-07-21
**Scope**: every mechanically checkable claim in `reports/2026-07-20-pdf-to-myst-fidelity.md`
**Tree state**: commit `ae23c52` on `main`, clean working tree
**Verdict**: all claims verified; zero discrepancies found — but see the
same-day addendum below: a sweep of components *outside* that report's scope
found three new defects, all fixed the same day

The fidelity report of 2026-07-20 documents the defects found in the PDF → MyST
conversion and asserts that every one of them is fixed. Since it was written,
three pull requests have landed (#9, #11, #12), the last of which renumbered
Chapter 7's equations. This report checks that the fidelity report's claims
hold for the tree as it stands now — that the fixes are still present, the
counts still exact, and the open items still accurately described.

It is a verification of the *repository against the report*, not a repeat of
the report's own audit. The distinction matters and is spelled out under "What
this verification did not re-check".

---

## Method

Six checks were run by six independent agents in parallel, each blind to the
others' results. Where a claim under test was about what the repo's own
validators report, the check re-ran those validators; where the claim was a
count or an inventory, the check recounted from scratch with freshly written
grep/Python one-liners rather than trusting `check_structure.py` to audit
itself. Line numbers quoted below were confirmed against the files by a
separate fact-checking pass after the six checks completed.

| # | Check | Result |
|---|---|---|
| 1 | Validation scripts (`check_structure.py`, `validate_prose.py`) | pass, zero drift |
| 2 | Inventory recount (equations, figures, footnotes, citations) | all five counts exact |
| 3 | Figure references vs files on disk | 48/48 resolve, no duplicates |
| 4 | Spot-check of the seven named defect fixes | 7/7 as claimed |
| 5 | Fresh `myst build --html` | exit 0, zero warnings |
| 6 | GitHub issue tracker vs "Still open" section | exact match |

---

## 1. Validation scripts

Both scripts exit 0. `check_structure.py` passes every assertion across the
seven chapters: 160 footnotes paired in both directions, 115 labelled
equations, 84 distinct `{eq}` reference targets (221 raw occurrences), 42
distinct `{numref}`/`{ref}` targets, 128 cited bib keys, 48 figures, no
heading absorbed into body text.

`validate_prose.py`, run against the source PDF, reproduces the fidelity
report's coverage table **exactly — zero drift in any cell**:

| Chapter | PDF words | MyST words | Coverage |
|---|---:|---:|---:|
| ch01 | 770 | 1,075 | 94.0% |
| ch02 | 4,896 | 4,891 | 86.8% |
| ch03 | 2,468 | 2,456 | 79.7% |
| ch04 | 3,726 | 3,690 | 80.5% |
| ch05 | 7,067 | 6,969 | 76.3% |
| ch06 | 2,332 | 2,310 | 77.8% |
| ch07 | 3,236 | 3,234 | 85.8% |
| **Total** | **24,495** | **24,625** | **81.3%** |

The validator flags 21 prose gaps and 0 maths gaps for review — the same
residual the fidelity report examined individually and attributed to text
inside figure images, OCR caption damage, and maths fragments, not to missing
prose.

## 2. Inventory recount

All five counts match the fidelity report exactly, recounted without using the
repo's scripts:

| Item | Claimed | Recounted |
|---|---:|---:|
| Labelled equations | 115 | 115 |
| Figure directives with labels | 48 | 48 |
| Footnote definitions | 160 | 160 (fn1–fn160, every marker paired) |
| Citation roles | 188 | 188 (179 `{cite:t}` + 9 `{cite:year}`) |
| Distinct bib keys cited | 128 of 198 | 128 of 198, none unresolvable |

Per-chapter equation maxima: ch02 18, ch03 19, ch04 14, ch05 44, ch06 9,
ch07 8 (ch01 has none). Every chapter's numeric sequence runs 1..max with no
gaps once the letter-suffixed labels the book itself uses (`eq-5-8b`,
`eq-5-17a`/`b`, `eq-6-2a`/`b`) are accounted for.

## 3. Figures on disk

All 48 figure directives (ch02–ch07; ch01 has none) resolve to files in
`paper/figures/`, and each image file is referenced exactly once — the
duplicate-image pattern behind the old fig-6-5e defect is absent. Specifically:

- The seven hand-named recovery crops (`fig-3-2`, `fig-4-4a`, `fig-4-4b`,
  `fig-5-8`, `fig-6-4b`, `fig-6-5e`, `fig-6-6c`) all exist and are referenced.
- `fig-6-5e` points at `figures/fig-6-5e.jpeg`; `fig-6-5d` at the distinct
  `figures/_page_161_Figure_4.jpeg`.
- `fig-5-10b`, one of the two figures the ch05 offset had hidden entirely, is
  present and resolves.

`paper/figures/` holds 56 files; the 8 unreferenced ones are cover and
back-matter page scans (`_page_1`, `_page_3`, `_page_198`–`_page_203`), not
lost chapter figures.

## 4. Spot-check of the named defect fixes

Each fix the fidelity report describes was located in the current files:

| Fix | Where found |
|---|---|
| Restored simulated-annealing footnote (book fn 11) | `ch04.md:302`, fn60 |
| Restored Calvo/Evans–Honkapohja–Sargent footnote (book fn 17) | `ch05.md:515`, fn89 |
| "replace (26)" cross-reference corrected to `eq-5-26` | `ch05.md:767` |
| ch07 renumbering: labels run exactly `eq-7-1`–`eq-7-8` | zero occurrences of `eq-7-9`/`eq-7-10` anywhere |
| Kuan–Liu forecast error uses η, not Latin `n` | `ch07.md:82`, `\eta_{t+1}` |
| eq-4-14's restored gradient companion, joined by "or" | `ch04.md:386–393`, `\tanh` with `\partial C(v_t)/\partial v_{it}` |

The one item the report leaves *open* was also confirmed to still be open, as
claimed: eq-5-13's display (`ch05.md:449`) has denominator `Nf(G_t)` while the
prose restatement (`ch05.md:461`) reproduces the book's printed
`Nf(G_{t+1})` — the internal contradiction issue #3 exists to adjudicate.

## 5. MyST build

`myst build --html`, run from the repo root with the same invocation CI uses
(`.github/workflows/validate.yml`), exits 0 and builds all 8 pages (`index.md`
plus ch01–ch07). CI's clean-build check — grepping the log for MyST's ⛔️/❌
markers — finds nothing. A broader case-insensitive grep for "warn"/"error"
matches only two Node.js runtime notices (an `ExperimentalWarning` about
localStorage and the `DEP0169` `url.parse()` deprecation), which come from the
Node runtime rather than the MyST build and also pass CI's check.

## 6. Issue tracker

The repository has seven issues, #2–#8 (#1 is a pull request). The mapping in
the fidelity report's "Still open" section holds exactly: #3 (silent
corrections of the printed page), #4 (thirteen page-qualified and multi-year
citations), #5 (possible missing Evans–Honkapohja–Sargent 1993 bib entry), #6
(70 uncited bibliography entries), #7 (two figures clipped in the source scan
itself), and #8 (figure directive style and figure-pair references) are all
open; #2 (Chapter 7's displaced equation numbering) is closed, consistent with
the report describing it as fixed.

---

## What this verification did not re-check

The fidelity report's equation and figure audit read every equation and figure
against 300 dpi renders of the page scans. This verification did **not**
repeat that visual comparison; it verified that the *outcomes* of that audit —
the fixes, the counts, the open items — are present in the current tree. The
visual audit's correctness rests on the 2026-07-20 report's own method
(three-refuter adversarial verification per discrepancy, second-agent
confirmation per re-crop), not on anything re-established here.

Prose coverage, by contrast, *was* re-established from scratch: the validator
re-ran against the PDF and reproduced the claimed table exactly.

---

## Conclusion

Every mechanically checkable claim in the 2026-07-20 fidelity report holds for
the current tree. The conversion stands as that report left it: prose complete
(the two dropped footnotes restored, word-count parity within a fraction of a
percent per chapter), equations exact in content and in numbering, all 160
footnotes and 188 citations resolving, all 48 figures present and correctly
paired, and a warning-free build.

What separates the MyST edition from a perfect replica of the printed book is
unchanged from the fidelity report's account: the editorial decisions tracked
in issues #3–#8, chiefly whether this edition reproduces the 1993 text as
printed or corrects it with a note, plus two tooling limits (`{cite:t}`'s
"&"-and-no-letter rendering, no locator syntax for page-qualified citations)
and two figures clipped in the source scan itself. None of these is missing or
inaccurate content; all are enumerated, tracked, and awaiting a policy call.

---

## Reproducing

The six checks used the repository's own entry points where they exist:

```bash
python scripts/check_structure.py             # structural assertions (no PDF needed)
uv run python scripts/validate_prose.py       # prose fidelity vs the PDF (needs source scan)
myst build --html                             # must exit 0 with no MyST warnings
gh issue list --state all                     # compare against "Still open" in the fidelity report
```

The inventory recount and defect spot-checks are grep-level checks over
`paper/*.md` and `paper/figures/`; the specific patterns are recorded in the
body of this report (labels `eq-N-M`, figure `:label:`/`:name:` directives,
`[^fnN]:` definitions, `{cite:` roles).

---

# Addendum (2026-07-21, same day): missing-components sweep

The verification above asks "do the fidelity report's claims hold?" This
addendum asks the complementary question: **what did no check ever look at?**
Four audits ran in parallel against the source scan: front matter, back
matter, page-attribution completeness, and an entry-by-entry comparison of
`paper/references.bib` against the printed reference list. They found three
defects in territory every prior check had skirted, all fixed the same day.

## Three new defects, fixed

### A. A dropped clause in ch06 footnote 137

The book's footnote (printed p. 151) ends "…low-frequency divergences in
exchange rates, *such as persistently different monetary and deficit
policies*." The MyST footnote ended at "exchange rates." — the closing clause
appeared nowhere in `paper/` (confirmed against both the OCR layer and a
visual render of scan p. 165). **Restored** in `ch06.md`.

How it survived every check is the instructive part: the footnote runs over
the page break onto ch06's nearly blank final page, and the ~8-word loss sits
below `validate_prose.py`'s `--min-run 20` reporting threshold. Page
attribution was correct, word-count parity barely moved, the build stayed
green. This **falsifies the 2026-07-20 report's "No dropped prose remains"**
— it is the third dropped-content instance overall and the first found after
that report — and the blind-spot class (short losses on sparse run-over
pages) is now tracked as issue #14.

### B. The `EvansSargent1993` bibliography entry dropped an author

Adjudicates issue #5, from a 250 dpi render of printed p. 174 rather than
OCR: the printed entry is three-authored. Following "Evans, George and
Honkapohja, Seppo (1992b)…", the list continues "—— —— (1992c)", "—— ——
(1993a)", "—— —— (1993b)", then "—— —— and Sargent, Thomas J. (1993)" — the
double dashes carry *both* prior authors. The bibliography entry was never
missing, as #5 hypothesised; it was present with Honkapohja dropped.
**Fixed**: renamed `EvansHonkapohjaSargent1993` (keeping the
surnames-plus-year key convention) with the author restored, and the
plain-text citation in ch05 fn89 — left unlinked pending exactly this check —
is now a `{cite:t}` role.

### C. The Arne Ryde memorial page was silently skipped

Scan p. 4 — "ARNE RYDE, 8 December 1944 – 1 April 1968" over a photograph —
appeared nowhere in the MyST edition, though the companion Foundation note
made it into `ch01.md`. The photograph had in fact been extracted by marker
(`figures/_page_3_Picture_0.jpeg`) and had sat unreferenced ever since.
**Restored** at the top of `ch01.md` as an unlabelled image with the name and
dates beneath, matching its frontispiece position in the book.

## Verified sound by the sweep

- **Page coverage is airtight.** Reproduced from `validate_prose.py`'s own
  attribution functions: ch01–ch07 occupy scan pages 15–184 contiguously,
  with zero unattributed interior pages and no boundary page shaved (ch02,
  ch05, and ch07 boundary sentences verified verbatim in the MyST; the other
  chapters' edges confirmed via their neighbours).
- **`references.bib` is a true transcription of the printed list.** All 198
  printed entries pair one-to-one with the 198 bib entries, in order; 197
  match on authors, year, disambiguation letter, and title, and the one
  mismatch is defect B above. Every a/b/c letter group aligns. The bib's
  apparent errors "Robbins, J." and "Litterman, F." are faithful
  reproductions of typos in the printed book (image-verified), which is
  correct behaviour for this project.
- **The orphan figure files are explained.** `_page_198`–`_page_202` are
  marker crops of blank endpapers; `_page_203_Figure_4.jpeg` is the
  back-cover barcode; `_page_3_Picture_0.jpeg` was the memorial photograph,
  now in use.
- **Front matter is otherwise complete**: dedication, Foundation note,
  Acknowledgements, and title-page metadata are all reproduced. Cover,
  half-title, and copyright page are absent as expected for a conversion (the
  ISBNs, 0-19-828864-6 hbk / 0-19-828869-7 pbk, are recorded nowhere and
  could cheaply live in `myst.yml`).

## Deviations found and filed, not fixed

- **Heading hierarchy** (#13): six headings the printed Contents indents as
  subsections are top-level `##` sections in the MyST files, and chapter H1
  numbering is inconsistent (`# 1 Introduction` / `# Adaptation…` unnumbered
  / `# 6. Experiments`). Mechanical to fix, but anchor slugs change, so it is
  filed rather than fixed inline.
- **"Heterassociation" → "Heteroassociation"** (`ch04.md:251`): a silent
  respelling of the printed heading, verified in both the printed Contents
  and body text. Added to issue #3's silent-corrections list.
- **Author and Subject Indexes** (#15): the book's two indexes (printed pp.
  181–184) have no MyST counterpart; `NOTES.md` records the omission as
  deliberate. Site search substitutes for the author index but not for the
  subject index's curated terms and see-also structure. Filed as a policy
  decision.
- **Uncited entries never render** (noted on #6): because MyST builds the
  bibliography from citations, the ~70 uncited entries appear on no page of
  the built site — the printed book's browsable standalone References
  section has no counterpart.

## Counts after the fixes

The verification body above describes the tree at `ae23c52`; the fixes in
this addendum supersede three of its numbers. Citation roles are now **189**
(was 188), distinct cited bib keys **129** (was 128), and figure references
**49**, of which 48 are labelled — the memorial image is deliberately
unlabelled, as it is a frontispiece plate rather than a numbered book figure.
Footnote and equation counts are unchanged. `check_structure.py` passes on
all assertions and `myst build --html` remains clean. The inventory table in
`NOTES.md` is updated to match.

## Limits of the sweep

Sub-threshold prose losses elsewhere cannot yet be excluded — defect A proves
the class exists, and #14 defines the pass that would close it. Bib title
comparison was done at the fragment level (first ~6 words), so a deep-in-title
wording difference in an otherwise-matched entry could escape notice. The six
heading-hierarchy findings rest on the printed Contents' indentation, which
was consistent across chapters, but body-page typography was verified only
for the Heterassociation case.
