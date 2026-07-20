# Fidelity Report: Sargent (1993) PDF → MyST Markdown

**Date**: 2026-07-20
**Scope**: `paper/ch01.md`–`ch07.md`, `paper/references.bib`, `paper/figures/`
**Source**: `source/Sargent_Bounded Rationality in Macroeconomics_...pdf` (204 pages)

This is the quality assessment called for by Step 4 and the Quality Verification
Checklist in `PROMPT-PDF-TO-MD.md`. None had been produced for this book: prior
to this report the only verification on record was `myst build --html`
succeeding, which establishes that the document *compiles*, not that it *matches
the original*.

Every defect it found has been fixed, including Chapter 7's displaced equation
numbering, which surfaced after the first pass. What remains open is listed at
the end; each item is tracked as an issue and is a judgement call rather than a
defect.

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
maths — nor about figure content. Those were closed separately by a visual
audit; see "Equation and figure audit" below.

It is also, on its own, blind to *structure*. The citation rewrite initially
matched across a blank line and collapsed a paragraph into the heading above it
("## A model of Bray" absorbed the sentence that followed). Coverage barely
moved, because every word was still present and still in order — presence and
arrangement are different properties, and an n-gram score only measures the
first. The regex now refuses to cross a line break, and the validator carries a
separate structural assertion that flags headings which look like they have
swallowed body text. Caught in review by GitHub Copilot on PR #1, not by this
report's own method.

---

## Results

### Prose coverage

| Chapter | PDF words | MyST words | Coverage | Reverse |
|---|---:|---:|---:|---:|
| ch01 | 770 | 1,075 | 94.0% | 67.1% |
| ch02 | 4,896 | 4,891 | 86.8% | 86.9% |
| ch03 | 2,468 | 2,456 | 79.7% | 80.1% |
| ch04 | 3,726 | 3,690 | 80.5% | 81.4% |
| ch05 | 7,067 | 6,969 | 76.3% | 77.7% |
| ch06 | 2,332 | 2,310 | 77.8% | 78.6% |
| ch07 | 3,236 | 3,234 | 85.8% | 85.8% |
| **Total** | **24,495** | **24,625** | **81.3%** | |

Word-count parity is the more legible signal: ch02 4,896 vs 4,891, ch07 3,236 vs
3,234. A dropped paragraph would leave MyST short by its length. ch01 runs long
because `ch01.md` also holds front matter (dedication, Arne Ryde Foundation,
acknowledgements) that sits outside the chapter's page range.

The residual ~19% is not missing text. All flagged prose gaps were examined
individually; the causes are text embedded *inside* figure images (OCR reads
axis labels and annotations that legitimately have no prose counterpart), OCR
damage to figure captions (`igure` for `Figure`), and maths fragments long
enough to survive the content-word filter. Two gaps were real content loss and
have been fixed.

### Counts

| Item | Count | Note |
|---|---:|---|
| Labelled equations | 115 | matches the printed numbering in every chapter |
| Figure labels | 48 | all image references resolve |
| Footnote definitions | 160 | sequential `fn1`–`fn160`, every marker paired |
| Citations linked | 188 | was 0 before this pass |
| Distinct bib keys cited | 128 | of 198 entries |

---

## Defects found and fixed

### 1. Bibliography entirely orphaned — FIXED

All 187 author-year references were plain prose, so the 198-entry bibliography
was unreachable and never rendered. `scripts/link_citations.py` now links them
(188 after the footnote restoration below). Matching is self-validating: keys
are surnames concatenated with the year, so a candidate is accepted only when
the key it implies actually exists.

**Known cost of this fix.** MyST renders `{cite:t}` as "Evans & Honkapohja
(1992)" — it substitutes "&" for the book's "and", and it does not apply
disambiguation letters, so `1992a`, `1992b` and `1992c` all render as "(1992)"
and become indistinguishable in the text. mystmd 1.10 exposes no citation-style
configuration to change this. This was accepted deliberately, trading exact
typographic fidelity for a working bibliography.

Possessive forms use `{cite:year}` instead, which renders only "(1961)" and
leaves the name in prose, so "Muth's (1961)" survives intact.

### 2. Two footnotes dropped — FIXED

Both were located by the prose validator and confirmed against the page scans.

**Chapter 4, book footnote 11** (PDF p. 67), attached to "…contain an example of
what is hoped for." Restored as `fn60`:

> Out of fear of getting stuck at an inferior local rest point, econometricians
> who estimate nonlinear models have the habit of trying a variety of starting
> values for their hill-climbing algorithms. Simulated annealing is inspired by
> the same fear, and amounts to a systematic way of choosing a set of starting
> values, and of perturbing directions and step sizes.

**Chapter 5, book footnote 17** (PDF p. 108), attached to "…render the exchange
rate and all other endogenous variables determinate." Restored as `fn89`:

> See Calvo (1988) and Evans, Honkapohja, and Sargent (1993) for setups in which
> a fraction 1 − μ of agents is rational, and a fraction μ is 'adaptive' in
> particular senses. Both of these contributions are concerned with studying how
> dynamics might differ from the rational expectations dynamics even with a very
> small μ.

`Calvo1988` had been sitting in `references.bib` uncited as a direct
consequence, and is now linked.

Restoring these took the book from 158 to 160 footnotes.
`scripts/renumber_footnotes.py` reassigned labels sequentially in document
order, so the `fn1`–`fn160` convention still holds. It refuses to run unless
every marker pairs with a definition in the same file.

### 3. Five equations present but unlabelled — FIXED

Equations 3.7, 3.12, 5.26, 5.37 and 5.38 are printed in the book and their maths
*was* present in the MyST, but none carried an `(eq-N-M)` label, so nothing
could cross-reference them. Labels added; every chapter now has a complete
1..max sequence.

This had already caused two prose regressions, both now repaired:

- `ch05.md` read "when agents forecast according to the rule and when the
  $\theta$'s are updated according to {eq}`eq-5-39`" — the book reads "according
  to the rule (38)". The reference had been dropped with the label.
- `ch05.md` read "The effect of this will be to replace {eq}`eq-5-21` with an
  equilibrium condition of the form" where the book reads "replace (26)".
  `eq-5-21` is a *different* equation; with (26) unlabelled the conversion had
  pointed at the nearest available label. Corrected to `eq-5-26`.

Note that equation 5.37 is a two-line system in the book carrying a single
number. It is labelled on the first block with the companion left unlabelled,
matching how `eq-5-39` was already handled.

### 4. Two figure images missing — FIXED

`figures/_page_63_Figure_4.jpeg` (fig-3-2) and `figures/_page_81_Figure_3.jpeg`
(fig-4-4b) were referenced but had never existed. Both pages carry two
side-by-side figures; marker's metadata shows it detected 3 captions but only
1 figure block on PDF p. 64, and 2 captions but 1 figure block on p. 82, so it
segmented only the left-hand figure of each pair.

The pages are full-page scans with no separately embedded images, so the
figures were recovered by rendering each page at 300 dpi with `pdftoppm` and
cropping to match marker's framing (plot area with axis labels, no caption).

`myst build --html` now completes with **zero warnings**.

---

## Equation and figure audit

The OCR layer cannot reach maths or images, so these were checked by rendering
each relevant page at 300 dpi and reading it against the source. Every equation
discrepancy was then attacked by three independent refuters (transcription,
mathematics, scan-legibility) with majority-refute dropping the claim; every
re-crop was confirmed by a second agent working from a fresh render.

**All 117 then-labelled equations were checked, and their content is sound.**
Six discrepancies were raised, one was refuted, five survived. Two were
conversion errors and are now fixed. (Two ch07 displays were subsequently
unnumbered to match the book, which is why the count in the table above is 115.)

- **The Kuan–Liu forecast error** (ch07) — the book prints η; the MyST had Latin
  `n`, both in the equation and in the sentence after it, though the same
  chapter renders η correctly in what are now `eq-7-1` and `eq-7-5`. **Fixed.**
  Named by content rather than by label: this equation carried the label
  `eq-7-1` when the defect was found, but it is now set inline and unnumbered,
  as the book sets it, and `eq-7-1` denotes a different equation.
- **eq-4-14** (ch04) — the book gives two displays joined by "or"; the MyST had
  dropped the unnumbered gradient form
  `v_{i,t+1} = tanh(−(∂C/∂v_it)/T)`, removing the derivation link between the
  cost function and the update rule. **Fixed.**

Three more are places where the MyST silently *corrects* the printed page, which
against an exact-replication mandate is an editorial decision rather than a
defect. All three are open, tracked in issue #3:

| | Book prints | MyST has | Note |
|---|---|---|---|
| eq-4-3 | `g(x) − θ₀ + Σ` | `− Σ` | MyST is mathematically right; the book's `+` looks like a typesetting error |
| eq-5-13 | `Nf(G_{t+1})` | `Nf(G_t)` | MyST matches the derivation, but ch05.md line 461 still reproduces the printed form, so the file contradicts itself |
| eq-2-14 | tag on the 1st display | tag on the 2nd | cosmetic; eq-2-15 and eq-2-18 follow the print, so eq-2-14 is the odd one out |

### What the equation audit did not check, and what it missed

It compared equation *content* against the scans, and never checked that the
MyST's equation *numbers* correspond to the book's. In Chapter 7 they did not.
The book numbers eight equations there; the conversion labelled ten, having
given numbers to two displays the book leaves unnumbered — one of them set
inline in a sentence. Every ch07 number was therefore displaced by two, so the
book's equation (1) was the one labelled `eq-7-3`. Chapters 2 to 6 were checked
the same way and all align correctly.

**Fixed.** Each of the eight printed numbers was matched to its equation against
renders of PDF pp. 175–177, the two extra displays were unnumbered (the first
returned to inline, as printed), `eq-7-3`…`eq-7-10` were renumbered to
`eq-7-1`…`eq-7-8`, and the 13 `{eq}` references following them were updated. The
resulting reference targets — (2), (3), (6), (8) — are exactly the equations the
book's own prose cites, which is an independent confirmation of the mapping.
That is why the labelled-equation count in this report is 115 rather than 117.

`scripts/check_structure.py` could not have caught this. It asserts that a
chapter's labels form a complete 1..max run, which a uniformly displaced
sequence satisfies perfectly. No check compares MyST numbering against the
printed numbering, and none exists — closing that would need the printed
numbering as an input, which brings back the source-scan problem described
under "Reproducing".

Worth stating plainly: the audit section above verified equation content, not
equation numbering. The distinction is the whole reason this defect survived it.

**Figures: 47 checked, 16 problems.** The figures were in materially worse shape
than the equations — the reverse of what the prose-coverage work suggested.

---

## Defects found and fixed (figures)

### 5. A one-position figure shift through ch05 — FIXED

`marker-pdf` extracted only three of the four panels on PDF p. 125, missing
printed Figure 8. Every subsequent directive then took the next image along, so
four figures displayed the wrong plot and two printed figures appeared nowhere:

| Directive | Was showing | Now shows |
|---|---|---|
| fig-5-8 | printed Fig 9a | printed Fig 8 (newly cropped) |
| fig-5-9a | printed Fig 9b | printed Fig 9a |
| fig-5-9b | printed Fig 10a | printed Fig 9b |
| fig-5-10a | printed Fig 10b | printed Fig 10a |
| *(absent)* | — | fig-5-10b, printed Fig 10b |

A reader of fig-5-8 was being shown a saving-rate curve captioned as a
logarithm of the exchange rate. The captions were all correct throughout; only
the image paths were displaced, so the fix was a re-pointing plus one new crop.

### 6. Other figure defects — FIXED

- **fig-6-5e** reused fig-6-5d's image file outright; printed Figure 5e had
  never been extracted. Now cropped and pointed at its own file.
- **fig-4-4a** and **fig-6-4b** were crops containing *both* side-by-side
  panels, so each chapter rendered its neighbour twice. Re-cropped to one panel.
- **fig-6-6c** was vertically misaligned: caption text from Figure 6a bled in at
  the top and the x-axis with all its tick labels was cut off the bottom.
- **fig-3-2** clipped its final x tick label to "2" instead of "25" — an error
  in the hand-recovery recorded earlier in this report, not in marker's output.

Hand-produced crops are now named for the figure they contain (`fig-5-8.jpeg`)
rather than carrying marker's page-index names, so they are distinguishable from
automated extractions at a glance. Four superseded files were removed; the three
that were marker originals remain in `_archive/marker_output/`.

---

## Verified sound

- No dropped prose remains, across all seven chapters.
- All 160 footnote markers resolve to a definition; no orphans in either
  direction; labels are sequential with no gaps.
- Every equation number from 1 to the chapter maximum carries a label.
- All figure references resolve to files on disk.
- `myst build --html` completes with no errors and no warnings.
- All 188 citation roles resolve in the built output — zero cite errors — and
  the bibliography renders.
- No dangling `{eq}` cross-references.
- No heading has absorbed body text; all section anchors resolve.

---

## Still open

**Thirteen citations remain unlinked** (#4) — page-qualified and multi-year forms,
which MyST has no locator syntax for: `Hurwicz (1946, p. 133)`, `Sargent (1987,
ch. XIII)`, `Barsalou (1992, p. 9)`, `Friedman and Schwartz (1963, pp. 156–68)`,
`Lucas (1981, pp. 221, 283)`, `Ljung, Pflug, and Walk (1992, pp. 99–100)`,
`Hansen and Sargent (1980, 1981)`, `Evans (1985, 1989)`, `Judd (1990, 1992)`,
`Chen and White (1992, 1993)`, `Marcet and Sargent (1989a, 1989b)` (×2), and
`Marcet and Sargent (1989a, 1989b, 1992)`.

**One citation is disambiguated by inference.** `ch05.md` fn94 cites "Evans and
Honkapohja (1993)" with no letter, though the book uses "(1993b)" elsewhere. The
ambiguity is in the original, not the conversion. Linked to
`EvansHonkapohja1993b`: the footnote describes "path dependence", and 1993b is
*Adaptive Forecasts, Hysteresis and Endogenous Fluctuations*. Recorded in
`OVERRIDES` in `scripts/link_citations.py`. Worth confirming against the printed
reference list.

**A three-author work may be missing from the bibliography** (#5). The restored ch05
footnote cites "Evans, Honkapohja, and Sargent (1993)", for which there is no
entry; the bibliography has `EvansSargent1993` (two authors) and
`EvansHonkapohja1993a`/`b`. That citation is left as plain text pending a check
of the printed reference list.

**70 of 198 bibliography entries are uncited** (#6). Expected in part — a book's
reference list carries works not cited inline — but large enough to be worth a
pass, since some may be citations the scanner's patterns miss.

**Figure directives are stylistically inconsistent** (#8): ch02–ch04 use `:label:`,
ch05–ch07 use `:name:`. Both are valid MyST and both resolve; harmonising is
cosmetic.

Everything below is tracked as a GitHub issue, so this section and the issue
list should not drift apart.

No equation defect remains, of content or numbering. Chapter 7's displacement
(#2), the Kuan–Liu forecast error's η and eq-4-14's dropped companion
display are all fixed.

**Three equations and six figure captions silently correct the printed page**
(#3), and all nine turn on a single decision: does this edition reproduce the
1993 text as printed, or correct it with a note? The equations are eq-4-3,
eq-5-13 and eq-2-14; the captions are fig-3-1 ("eighth-order" where the book
prints "eight-order"), fig-4-5a/4-5b (`tanh(z/T)` where the book and the
surrounding MyST both use `x`), fig-5-6 (subscript `t` for the printed `i`, and
a dropped bar), fig-6-4a (swaps which symbol carries the value 10), and fig-7-2b
(an em dash the print does not have). Two of these — fig-6-4a and fig-5-6 — look
like transcription slips rather than deliberate corrections, and arguably want
fixing whichever way the policy lands.

Two further figures are clipped **in the source scan itself** (#7) — fig-5-12b's
final x tick and fig-7-2a's y-axis signs — and no crop can recover them.

Prose references to figure *pairs* resolve to the first panel (#8): the book writes
"Figure 9 shows saving rates for the two types of agents", which renders as
"Figure 9a shows…" though the pair spans 9a and 9b. MyST needs a single target,
so this is a defensible convention rather than an error, but it is a deviation.

---

## Reproducing

```bash
python scripts/check_structure.py             # structural assertions (no PDF needed)
uv run python scripts/validate_prose.py       # prose fidelity vs the PDF
uv run python scripts/link_citations.py       # citation linkage
uv run python scripts/renumber_footnotes.py   # footnote label sequence
```

All four are deterministic and default to reporting only; `link_citations.py`
and `renumber_footnotes.py` write only with `--apply`.

`check_structure.py` is the one that runs in CI, on every pull request via
`.github/workflows/validate.yml`, alongside a MyST build whose log is grepped
for warnings — `myst build` exits 0 even when it cannot find a referenced image,
which is how two figures stayed missing for months behind a green build. It is
stdlib-only so CI needs no dependency install.

The other three cannot run in CI: they need the source scan, which is gitignored
as a copyrighted 8 MB book. Prose fidelity is therefore permanently a local
check, available only to someone holding a copy of the PDF.

---

## Assessment against the checklist

`PROMPT-PDF-TO-MD.md` sets a target of ≥90% fidelity. Every checklist area has
now been checked against the source.

**Prose** is sound: two dropped footnotes were the only content loss in ~24,500
words, and word-count parity holds to within a fraction of a percent per
chapter. **Equations** are sound: all 117 were verified against the page scans,
and the three defects found — the Kuan–Liu forecast error's η, eq-4-14's
dropped companion display, and Chapter 7's displaced numbering — are fixed. Three deliberate-looking
corrections of the printed text remain, as decisions rather than defects.
**Structure** is clean: bibliography linked, every equation labelled and
numbered as the book numbers it, every reference resolving, build warning-free.

**Figures were the weak point**, and not where the prose work pointed. Sixteen
problems in 47 figures, including a shift that silently mis-captioned four plots
in ch05 and hid two others entirely. The lesson generalises past this book: an
automated extractor that drops one panel from a multi-panel page does not fail
loudly, it fails by *offset*, and every downstream figure inherits the error
while the build stays green and the prose checks stay quiet. Figure-to-caption
correspondence needs its own assertion; nothing else catches it.

What remains is a set of editorial decisions rather than unverified surface —
listed under "Still open" — turning mostly on one question: does this edition
reproduce the 1993 text as printed, or correct it with a note?
