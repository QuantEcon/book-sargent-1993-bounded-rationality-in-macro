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

| Chapter | File | Status | Lines | Details |
|---------|------|--------|-------|---------|
| Front matter + Ch 1: Introduction | `ch01.md` | ✅ Complete | 72 | Dedication, Arne Ryde Foundation, Acknowledgements, Introduction |
| Ch 2: Expectations and Behavior | `ch02.md` | ✅ Complete | 457 | eq-2-1 to eq-2-18, fig-2-1/2-2, fn1–fn25 |
| Ch 3: Data Structures | `ch03.md` | ✅ Complete | 431 | eq-3-1 to eq-3-19, fig-3-1/3-2, fn26–fn52 |
| Ch 4: Networks and AI | `ch04.md` | ✅ Complete | 540 | eq-4-1 to eq-4-14, fig-4-1 to fig-4-5b, fn53–fn71 |
| Ch 5: Adaptation in Artificial Economies | `ch05.md` | ✅ Complete | 1,122 | eq-5-1 to eq-5-44, fig-5-1 to fig-5-13b, fn72–fn117 |
| Ch 6: Experiments | `ch06.md` | ✅ Complete | 291 | eq-6-1 to eq-6-9, fig-6-1 to fig-6-7, fn118–fn135 |
| Ch 7: Applications | `ch07.md` | ✅ Complete | 262 | eq-7-1 to eq-7-10, fig-7-1 to fig-7-2b, fn136–fn158 |
| References | `references.bib` | ✅ Complete | 1,660 | 198 BibTeX entries |
| Indexes | — | Omitted | — | Not needed — MyST auto-generates navigation |

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
