# Fidelity Report: Sargent (1993) PDF → MyST Markdown

**Date**: 2026-07-20
**Scope**: `paper/ch01.md`–`ch07.md`, `paper/references.bib`
**Source**: `source/Sargent_Bounded Rationality in Macroeconomics_...pdf` (204 pages)

This is the quality assessment called for by Step 4 and the Quality Verification
Checklist in `PROMPT-PDF-TO-MD.md`. None had been produced for this book: prior
to this report the only verification on record was `myst build --html`
succeeding, which establishes that the document *compiles*, not that it *matches
the original*.

---

## Method

The source PDF is a scan, but it carries an OCR text layer that `pdftotext`
extracts cleanly (~329k characters). That layer is an independent channel: it
does not pass through `marker-pdf`, so content marker dropped is still visible
in it. This matters because the conversion worked from marker's output rather
than from the PDF, meaning nothing marker lost could be detected anywhere else
in the pipeline.

`scripts/validate_prose.py` attributes PDF pages to chapters, strips page
furniture, and measures what fraction of the PDF's 8-grams appear anywhere in
the corresponding MyST chapter. Coverage is computed over *content words*
(alphabetic, ≥4 characters) because OCR renders equations as short digit-laden
fragments; including them made the score track maths density rather than
fidelity. Matching is order-insensitive, so footnotes moving from page-bottom to
inline definitions do not register as loss.

**What this method does and does not establish.** It is good evidence about
prose presence. It says nothing about equation *correctness* — the OCR garbles
maths — nor about figure content, nor about whether numerals within equations
are right. Those still require visual comparison against the PDF.

---

## Results

### Prose coverage

| Chapter | PDF words | MyST words | Coverage | Reverse |
|---|---:|---:|---:|---:|
| ch01 | 770 | 1,075 | 93.2% | 66.6% |
| ch02 | 4,896 | 4,891 | 86.7% | 86.8% |
| ch03 | 2,468 | 2,456 | 79.7% | 80.1% |
| ch04 | 3,726 | 3,655 | 79.6% | 81.2% |
| ch05 | 7,073 | 6,936 | 75.7% | 77.5% |
| ch06 | 2,332 | 2,310 | 77.8% | 78.5% |
| ch07 | 3,236 | 3,234 | 85.7% | 85.7% |
| **Total** | **24,501** | **24,557** | **81.0%** | |

Word-count parity is the more legible signal: ch02 4,896 vs 4,891, ch07 3,236 vs
3,234. A dropped paragraph would leave MyST short by its length. ch01 runs long
because `ch01.md` also holds front matter (dedication, Arne Ryde Foundation,
acknowledgements) that sits outside the chapter's page range.

The residual ~19% is not missing text. Every one of the 22 flagged prose gaps
was re-examined individually; the causes are text embedded *inside* figure
images (OCR reads axis labels and annotations that legitimately have no prose
counterpart), OCR damage to figure captions (`igure` for `Figure`), and maths
fragments long enough to survive the content-word filter. Two gaps were real,
and are recorded below.

### Counts

| Item | Measured | Notes |
|---|---:|---|
| Labelled equations | 112 | 5 further equations present but unlabelled |
| Figure labels | 47 | 52 image files on disk |
| Footnote definitions | 158 | every marker resolves to a definition |
| Citations linked | 187 | was 0 before this pass |
| Distinct bib keys cited | 127 | of 198 entries |

---

## Defects found

### 1. Two footnotes dropped (content loss) — OPEN

Both were located by the prose validator and confirmed against the PDF.

**Chapter 4, PDF footnote 11** — absent from `ch04.md`:

> Out of fear of getting stuck at an inferior local rest point, econometricians
> who estimate nonlinear models have the habit of trying a variety of starting
> values for their hill-climbing algorithms. Simulated annealing is inspired by
> the same fear, and amounts to a systematic way of choosing a set of starting
> values, and of perturbing directions and step sizes.

**Chapter 5, PDF footnote 17** — absent from `ch05.md`:

> See Calvo (1988) and Evans, Honkapohja, and Sargent (1993) for setups in which
> a fraction 1 − ρ of agents is rational, and a fraction γ is 'adaptive' in
> particular senses. Both of these contributions are concerned with studying how
> dynamics might differ from the rational expectations dynamics even with a very
> small ρ.

`Calvo1988` sits in `references.bib` uncited as a direct consequence. The second
footnote also cites "Evans, Honkapohja, and Sargent (1993)", a three-author work
with no corresponding entry — the bibliography has `EvansSargent1993` (two
authors) and `EvansHonkapohja1993a`/`b`. Whether these are the same work needs
checking against the printed reference list.

Restoring these requires deciding where the markers attach and whether to keep
the sequential `fn1`–`fn158` labelling convention (MyST numbers footnotes at
render time, so labels are arbitrary identifiers and no renumbering is strictly
required). Left open as an editorial call.

### 2. Five equations present but unlabelled — OPEN

Equations 3.7, 3.12, 5.26, 5.37 and 5.38 are printed in the book and their maths
*is* present in the MyST, but none carries an `(eq-N-M)` label, so nothing can
cross-reference them. This is a cross-referencing defect, not content loss.

It has already caused one prose regression. `ch05.md` reads:

> when agents forecast according to the rule and when the $\theta$'s are updated
> according to {eq}`eq-5-39`

where the book reads "according to the rule (38)". The reference was dropped
along with the label.

Two related notes: equation 5.37 is a two-line system in the book and appears in
MyST as two separate unlabelled blocks; and the `[^fn107]` definition in
`ch05.md` is interleaved between a sentence and the equation it introduces,
splitting them.

### 3. Two figure images missing — OPEN (previously known)

`figures/_page_63_Figure_4.jpeg` (fig-3-2) and `figures/_page_81_Figure_3.jpeg`
(fig-4-4b). `marker-pdf` extracted only the first figure from each of those two
pages. These are the only warnings `myst build` emits.

### 4. Bibliography entirely orphaned — FIXED

All 187 author-year references were plain prose, so the 198-entry bibliography
was unreachable and never rendered. `scripts/link_citations.py` now links all
187 (127 distinct keys). Matching is self-validating: keys are surnames
concatenated with the year, so a candidate is accepted only when the key it
implies actually exists.

**Known cost of this fix.** MyST renders `{cite:t}` as "Evans & Honkapohja
(1992)" — it substitutes "&" for the book's "and", and it does not apply
disambiguation letters, so `1992a`, `1992b` and `1992c` all render as "(1992)"
and become indistinguishable in the text. mystmd 1.10 exposes no citation-style
configuration to change this. This was accepted deliberately, trading exact
typographic fidelity for a working bibliography.

Possessive forms use `{cite:year}` instead, which renders only "(1961)" and
leaves the name in prose, so "Muth's (1961)" survives intact.

### 5. Thirteen citations still unlinked — OPEN

Page-qualified and multi-year forms, which MyST has no locator syntax for:
`Hurwicz (1946, p. 133)`, `Sargent (1987, ch. XIII)`, `Barsalou (1992, p. 9)`,
`Friedman and Schwartz (1963, pp. 156–68)`, `Lucas (1981, pp. 221, 283)`,
`Ljung, Pflug, and Walk (1992, pp. 99–100)`, `Hansen and Sargent (1980, 1981)`,
`Evans (1985, 1989)`, `Judd (1990, 1992)`, `Chen and White (1992, 1993)`,
`Marcet and Sargent (1989a, 1989b)` (×2), `Marcet and Sargent (1989a, 1989b,
1992)`.

### 6. One ambiguous citation — inferred

`ch05.md` fn92 cites "Evans and Honkapohja (1993)" with no letter, though the
book uses "(1993b)" elsewhere (fn81). The ambiguity is in the original, not the
conversion. Linked to `EvansHonkapohja1993b`: the footnote describes "path
dependence", and 1993b is *Adaptive Forecasts, Hysteresis and Endogenous
Fluctuations*. Worth confirming against the printed reference list. Recorded in
`OVERRIDES` in `scripts/link_citations.py`.

### 7. 71 of 198 bibliography entries uncited

Expected in part — a book's reference list carries works not cited inline — but
the figure is large enough to be worth a pass, since some may be citations the
scanner's patterns miss.

---

## Verified sound

- No dropped prose beyond the two footnotes above, across all seven chapters.
- All 158 footnote markers resolve to a definition; no orphans in either
  direction.
- `myst build --html` completes with no errors and no unresolved cross-
  references; the only warnings are the two missing images.
- All 187 citation roles resolve in the built output — zero cite errors — and
  the bibliography renders.
- No dangling `{eq}` cross-references: all 82 resolve to a defined label.

---

## Reproducing

```bash
uv run python scripts/validate_prose.py      # prose fidelity vs the PDF
uv run python scripts/link_citations.py      # citation linkage (dry run)
```

Both are deterministic and safe to re-run; `link_citations.py` only writes with
`--apply`.

---

## Assessment against the checklist

`PROMPT-PDF-TO-MD.md` sets a target of ≥90% fidelity. On prose the conversion is
sound — the two dropped footnotes are the only content loss found in ~24,500
words, and word-count parity holds to within a fraction of a percent per
chapter. The open items are structural rather than textual: five unlabelled
equations, two missing images, and thirteen unlinked qualified citations.

The checklist items that remain genuinely unverified are the ones this method
cannot reach: **equation correctness and figure content**. The OCR layer garbles
maths and cannot see inside images. Confirming those still requires reading the
PDF against the rendered HTML.
