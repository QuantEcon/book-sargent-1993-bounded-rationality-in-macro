# Conversion Notes: Sargent (1993) — Bounded Rationality in Macroeconomics

## Project

Converting the 204-page book from PDF to high-fidelity MyST Markdown, following the workflow in `PROMPT-PDF-TO-MD.md`.

---

## Step 1: marker-pdf Extraction

- **Date**: 2026-04-09
- **Tool**: `marker-pdf` v1.10.2 via `uv run marker_single`
- **Runtime**: ~3,830 seconds (~64 minutes) on macOS (CPU-bound — MPS not supported for table model)
- **Output**: `_archive/marker_output/Sargent_Bounded Rationality in Macroeconomics_ The Arne Ryde_Thomas J_ Sargent/`
  - 3,444 lines / ~347 KB of raw Markdown
  - 51 JPEG images extracted
  - 1 metadata JSON

### Extraction Quality Assessment

| Area | Quality | Notes |
|------|---------|-------|
| Prose | Good | Clean text, minor OCR issues (`0x2 6DP` for Oxford postcode `OX2 6DP`, `tt` for `it`) |
| Equations | Good | LaTeX mostly intact with `$...$` and `$$...$$` blocks |
| Table of Contents | Partial | Page numbers garbled in places (`DD.`, `o7`, `Sie)`, `eles`) |
| Figures | Good | 51 images — charts, diagrams, book covers |
| References | Good | Full bibliography extracted cleanly |
| Indexes | Fair | Author & Subject indexes extracted but table format messy |
| Footnotes | Good | Captured with `<sup>` tags, content present |

### OCR Errors Noted
- `0x2 6DP` → `OX2 6DP` (Oxford postcode)
- `tt` → `it` (copyright page)
- Various garbled page numbers in TOC (cosmetic)
- Some equation artifacts (e.g., `/'z` instead of proper LaTeX)

---

## Step 2: Project Structure Setup

- **Date**: 2026-04-09
- Created `paper/paper.md`, `paper/figures/`, `paper/references.bib`
- Using `uv` for repo-level Python environment (`pyproject.toml` + `uv.lock`)
- Dependencies: numpy, matplotlib, marker-pdf

---

## Step 3: MyST Conversion

- **Date**: 2026-04-09
- Converting marker output to MyST Markdown following PROMPT-PDF-TO-MD.md rules
- Working chapter by chapter through the book

### Book Structure (from original)
1. Introduction (pp. 1–8)
2. Expectations and Behavior (pp. 9–34)
3. Data Structures (pp. 35–53)
4. Networks and Artificial Intelligence (pp. 54–81)
5. Adaptation in Artificial Economies (pp. 82–134)
6. Experiments (pp. 135–151)
7. Applications (pp. 152–170)
8. References (pp. 171–180)
9. Author Index (pp. 181–182)
10. Subject Index (pp. 183–186)

### Conversion Progress

Counts below are **measured** from the files (see
`reports/2026-07-20-pdf-to-myst-fidelity.md`), not estimated. An earlier version
of this table was written from the conversion plan and disagreed with the actual
content — e.g. it claimed `fn1–fn25` for ch02, which really holds 32 footnotes.

| Chapter | File | Lines | Labelled eqs | Figure labels | Footnotes | Citations |
|---------|------|------:|------:|------:|------:|------:|
| Front matter + Ch 1: Introduction | `ch01.md` | 66 | 0 | 0 | 2 | 10 |
| Ch 2: Expectations and Behavior | `ch02.md` | 457 | 18 | 2 | 32 | 30 |
| Ch 3: Data Structures | `ch03.md` | 431 | 19 | 2 | 15 | 27 |
| Ch 4: Networks and AI | `ch04.md` | 542 | 14 | 7 | 23 | 18 |
| Ch 5: Adaptation in Artificial Economies | `ch05.md` | 1,122 | 46 | 18 | 47 | 61 |
| Ch 6: Experiments | `ch06.md` | 291 | 10 | 15 | 18 | 17 |
| Ch 7: Applications | `ch07.md` | 260 | 8 | 3 | 23 | 25 |
| **Total** | | **3,169** | **115** | **48** | **160** | **188** |
| References | `references.bib` | 1,660 | — | — | — | 198 entries |
| Indexes | — | — | — | — | — | Omitted; MyST generates navigation |

Every equation number from 1 to each chapter's maximum now carries a label,
every footnote marker pairs with a definition (`fn1`–`fn160`, no gaps), and
every figure reference resolves to a file. `myst build --html` is warning-free.

### MyST Conventions Used

- **Labels**: `(sec-slug)=` for section targets
- **Equations**: `$$ (eq-N-M)` numbered equations with `{eq}` cross-refs
- **Footnotes**: `[^fnN]` with inline definitions
- **Figures**: `:::{figure}` directives with `:label: fig-N-M`
- **Cross-refs**: `{numref}` for figures, `{eq}` for equations

---

## Step 4: References

- **Date**: 2026-04-09
- Built `paper/references.bib` with 198 BibTeX entries (1,660 lines)
- Entry types: `@article`, `@book`, `@incollection`, `@inproceedings`, `@phdthesis`, `@unpublished`
- Cite keys use `AuthorYear` format with lowercase suffixes for disambiguation (e.g., `Arifovic1992a`, `EvansHonkapohja1992b`)
- Disambiguated first-name keys where needed (e.g., `FriedmanD1991` vs `FriedmanM1953`, `SmithB1988` vs `SmithJM1982`)
- LaTeX-encoded special characters (e.g., `M{\'e}tivier`, `S{\"o}derstr{\"o}m`)
- Already wired into `myst.yml` via `bibliography: paper/references.bib`

---

## Step 5: Build & Verify

Note: this step establishes only that the document *compiles*. It is not a
fidelity check. For verification against the source PDF see Step 7.

- **Date**: 2026-04-09
- `myst build --html` — all 8 pages build successfully
- Base URL confirmed working: `BASE_URL=/paper.sargent-1993.bounded-rationality-in-macro`
- `myst.yml` has `base_url` under `site.options` — compatible with gh-pages

### Build Warnings (2 remaining)

| Warning | Cause |
|---------|-------|
| `paper/ch03.md` Cannot find image `figures/_page_63_Figure_4.jpeg` | marker-pdf did not extract second figure from page 63 (fig-3-2) |
| `paper/ch04.md` Cannot find image `figures/_page_81_Figure_3.jpeg` | marker-pdf did not extract second figure from page 81 (fig-4-4b) |

These two images need to be manually extracted from the source PDF.

---

## Step 6: GitHub Pages Deployment

- **Date**: 2026-04-09
- Created `.github/workflows/deploy.yml`
- Workflow: checkout → setup node 18.x → install mystmd → `myst build --html` → upload artifact → deploy to gh-pages
- Uses `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v4`
- `BASE_URL` env var set to `/${{ github.event.repository.name }}`
- Requires enabling GitHub Pages (source: GitHub Actions) in repo settings after first push

---

## Step 7: Validation Against the Source PDF

- **Date**: 2026-07-20
- Report: `reports/2026-07-20-pdf-to-myst-fidelity.md`

The source PDF is a scan but carries an OCR text layer that `pdftotext` reads
cleanly. That gives an independent check on the conversion, because it does not
pass through `marker-pdf` — anything marker dropped is invisible to every other
step of the pipeline, since the conversion worked from marker's output rather
than from the PDF.

- `scripts/validate_prose.py` — n-gram coverage of PDF text vs each MyST
  chapter. Result: 81.0% content-word coverage, with word-count parity per
  chapter. Every flagged gap was reviewed; two turned out to be real.
- `scripts/link_citations.py` — links plain-text author-year references to
  `references.bib`.

- `scripts/renumber_footnotes.py` — keeps footnote labels sequential in
  document order after an insertion.

Found and fixed:

- **Bibliography was entirely orphaned.** All 187 citations were plain prose, so
  the 198-entry bibliography never rendered. Now linked. Cost: MyST renders
  `{cite:t}` with "&" rather than "and" and drops a/b/c disambiguation letters;
  mystmd 1.10 has no setting for this. Accepted deliberately.
- **Two footnotes dropped entirely** — book fn11 in ch04 and fn17 in ch05, the
  only prose loss found. Restored; the book has 160 footnotes, not 158.
- **Five equations present but unlabelled** (3.7, 3.12, 5.26, 5.37, 5.38).
  Labelled. This had also produced two bad cross-references in ch05, including
  one pointing at the wrong equation (`eq-5-21` where the book says (26)).
- **Two figure images never extracted.** Recovered by rendering the pages at
  300 dpi and cropping; marker had segmented only the left figure of each
  side-by-side pair. The build is now warning-free.

Still open:

- Thirteen page-qualified/multi-year citations MyST cannot express.
- "Evans, Honkapohja, and Sargent (1993)" has no bibliography entry.
- 70 of 198 bibliography entries uncited.

---

## Step 8: Equation and Figure Audit

- **Date**: 2026-07-20
- Same report: `reports/2026-07-20-pdf-to-myst-fidelity.md`

The OCR layer cannot reach maths or images, so every equation and figure was
checked by rendering its page at 300 dpi and reading it against the source.
Equation discrepancies were then attacked by three independent refuters before
being believed; each re-crop was confirmed by a second pass from a fresh render.

**Equations: 117 of 117 verified; the content is sound.** Six discrepancies
raised, one refuted, five survived. The two conversion errors are now fixed —
eq-7-1, where the book prints η and the MyST had `n`, and eq-4-14, which had
dropped its companion display. Three silent corrections of the printed page
remain open (eq-4-3, eq-5-13, eq-2-14), tracked in issue #3.

The audit checked equation *content*, not equation *numbering*, and Chapter 7's
numbering turned out to be displaced by two: the book numbers eight equations
there while the conversion labelled ten, having numbered two displays the book
leaves unnumbered. Fixed (#2) by matching each printed number against renders of
PDF pp. 175-177, unnumbering the two extras and returning the first to the
inline form the book uses, then renumbering the rest and updating the 13 `{eq}`
references. The chapter's labelled equations therefore fall from 10 to 8, and
the book's total from 117 to 115.

`scripts/check_structure.py` could not have caught this: it asserts only that
each chapter's labels form a complete 1..max run, which a uniformly displaced
sequence satisfies. No check compares MyST numbering against the printed
numbering, and closing that gap would need the source scan as an input.

**Figures: 47 checked, 16 problems — the weak point of the conversion.** Fixed:

- A one-position shift through ch05. marker extracted three of the four panels
  on PDF p. 125, missing printed Figure 8, and every later directive took the
  next image along: four figures showed the wrong plot and two printed figures
  appeared nowhere. fig-5-8 was captioned as an exchange rate while showing a
  saving rate. Captions were all correct, so the fix was re-pointing plus one
  new crop, and fig-5-10b was added.
- fig-6-5e reused fig-6-5d's file; printed Figure 5e had never been extracted.
- fig-4-4a and fig-6-4b each contained both side-by-side panels.
- fig-6-6c was misaligned, bleeding in caption text and losing its x-axis.
- fig-3-2 clipped a tick label — an error in the earlier hand-recovery.

Hand-produced crops are now named for the figure they contain (`fig-5-8.jpeg`)
rather than marker's page-index names, so they are distinguishable at a glance.

Worth carrying forward: an extractor that drops one panel from a multi-panel
page fails by *offset*, not loudly. Every downstream figure inherits the error
while the build stays green and prose checks stay quiet. Figure-to-caption
correspondence needs its own assertion.

Still open, each tracked as a GitHub issue so this file and the issue list do
not drift apart: three equations
and six figure captions that silently correct the printed page (#3), all turning
on whether this edition reproduces the 1993 text as printed or corrects it with
a note; thirteen page-qualified and multi-year citations MyST cannot express
(#4); a cited three-author work with no bibliography entry (#5); 70 of 198
entries uncited (#6); two figures clipped in the source scan itself and
unrecoverable by any crop (#7); and minor directive-style and
figure-pair-reference inconsistencies (#8).

---

## File Inventory

| Path | Description |
|------|-------------|
| `myst.yml` | MyST project config with TOC for ch01–ch07 |
| `index.md` | Landing page |
| `paper/ch01.md` | Front matter + Chapter 1 |
| `paper/ch02.md` | Chapter 2 |
| `paper/ch03.md` | Chapter 3 |
| `paper/ch04.md` | Chapter 4 |
| `paper/ch05.md` | Chapter 5 |
| `paper/ch06.md` | Chapter 6 |
| `paper/ch07.md` | Chapter 7 |
| `paper/references.bib` | 198 BibTeX entries |
| `paper/figures/` | 51 JPEG images from marker extraction |
| `paper/_paper_combined.md` | Archived original combined file |
| `scripts/validate_prose.py` | Prose fidelity check against the PDF text layer |
| `scripts/link_citations.py` | Links author-year references to `references.bib` |
| `reports/` | Fidelity reports |
| `.github/workflows/deploy.yml` | GitHub Pages deployment workflow |
| `source/` | Original PDF |
| `_archive/marker_output/` | Raw marker-pdf extraction output |
| `PROMPT-PDF-TO-MD.md` | Conversion instructions/prompt |

---

## Lessons Learned

- **marker-pdf** occasionally misses extracting the second figure from a page (2 of 51 images missing)
- Splitting into per-chapter files is essential for conversion quality — keeps context manageable
- `BASE_URL` env var and `site.options.base_url` in `myst.yml` both work for gh-pages; the env var in the workflow serves as a reliable override
- Chapter 5 is by far the largest (~1,100 lines) covering the core technical material on adaptation algorithms
