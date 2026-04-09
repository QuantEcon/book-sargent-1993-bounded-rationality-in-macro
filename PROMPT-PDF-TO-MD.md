# PROMPT: Convert Academic PDF to High-Fidelity MyST Markdown

## Purpose

This prompt describes the tools and workflow for converting an older academic PDF paper into a high-fidelity MyST Markdown document. The emphasis is on **exact replication** of the original paper — same section numbering, table numbering, figure numbering, equation numbering, footnotes, and prose. The output should be a faithful digital representation of the original PDF, not an improved or restructured version.

This workflow assumes you are operating inside an IDE (VS Code + Copilot) with access to CLI tools via the terminal.

---

## Tools

| Tool | Role | Install |
|------|------|---------|
| `uv` | Python package & environment manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `marker-pdf` | PDF → raw Markdown extraction (text, equations, images) | `uv add marker-pdf` (or listed in `pyproject.toml`) |
| LLM (Claude / GPT) | Raw Markdown → MyST Markdown conversion, QA, cross-referencing | Available in IDE |
| `mystmd` | Build & verify MyST output (HTML, PDF) | `npm install -g mystmd` |

No other tools are required. `marker-pdf` handles OCR, equation extraction, and image extraction in one pass.

### Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install all dependencies
uv sync
```

This creates a `.venv/` inside the repo with all Python dependencies (numpy, matplotlib, marker-pdf, etc.) isolated from other projects. Use `uv run <command>` to run tools in the environment.

---

## Workflow

### Step 1: Run `marker-pdf` on the source PDF

```bash
uv run marker_single <input.pdf> --output_dir _archive/marker_output/
```

This produces:
- **`<name>.md`** — Raw Markdown with extracted text, equations, and image references
- **`<name>_meta.json`** — Structural metadata (table of contents, page-level bounding boxes)
- **`*.jpeg` / `*.png`** — Extracted figures and diagrams

Review the output for:
- OCR errors in text (especially author names, institution names, mathematical symbols)
- Missing or broken equations
- Extracted images — verify they correspond to actual figures in the paper

### Step 2: Set up project structure

Choose your file organization based on document length and structure:

**Single-file** (articles, short papers ≤ ~10 pages):

```
paper/
  paper.md          # MyST Markdown output
  references.bib    # BibTeX bibliography
  figures/           # Extracted/recreated figures
myst.yml            # MyST project configuration
```

**Multi-chapter** (books, monographs, long papers > ~10 pages with chapters):

```
paper/
  ch01.md           # Front matter + Chapter 1
  ch02.md           # Chapter 2
  ch03.md           # Chapter 3
  ...               # One file per chapter
  references.bib    # BibTeX bibliography
  figures/           # Extracted/recreated figures
myst.yml            # MyST project configuration
```

The multi-chapter approach is strongly recommended for longer documents because:
- It keeps each conversion task within LLM context limits
- Chapters can be converted independently (and in parallel via subagents)
- Errors are isolated to individual chapters rather than cascading
- Easier to review and QA section by section

Copy extracted images from `marker_output/` into `paper/figures/`. You may keep the marker-generated names (e.g., `_page_11_Figure_2.jpeg`) or rename to descriptive names.

Create `myst.yml`. For **single-file** projects:

```yaml
version: 1
project:
  title: "<Paper Title>"
  authors:
    - name: <Author 1>
    - name: <Author 2>
  bibliography:
    - paper/references.bib
  toc:
    - file: paper/paper.md
site:
  template: book-theme
```

For **multi-chapter** projects:

```yaml
version: 1
project:
  title: "<Book/Paper Title>"
  authors:
    - name: <Author 1>
  bibliography:
    - paper/references.bib
  toc:
    - file: index.md
    - title: Paper
      children:
        - file: paper/ch01.md
          title: "1 Introduction"
        - file: paper/ch02.md
          title: "2 Chapter Title"
        # ... one entry per chapter
site:
  template: book-theme
  options:
    base_url: /<repository-name>
```

Note: Only `ch01.md` needs the full YAML frontmatter (title, authors, date, bibliography). Subsequent chapter files need only the chapter title in frontmatter or can start directly with the chapter heading.

### Step 3: Convert marker output to MyST Markdown

Using the LLM, convert the raw marker Markdown into properly formatted MyST Markdown. For **multi-chapter** projects, work one chapter at a time — provide the LLM with the relevant portion of the marker output for each chapter.

Provide the LLM with:

1. The raw marker output (`<name>.md`) — or the relevant chapter portion
2. The original PDF (for visual verification of tables, equations, and layout)
3. The instructions below

**Numbering convention for multi-chapter projects:** Use chapter-scoped label prefixes:
- Equations: `(eq-2-1)`, `(eq-2-2)`, ... for Chapter 2
- Figures: `fig-3-1`, `fig-3-2`, ... for Chapter 3
- Footnotes: Number sequentially across the entire document (`[^fn1]` through `[^fnN]`)

#### LLM Conversion Instructions

> You are converting a raw Markdown extraction of an academic paper into high-fidelity MyST Markdown. Your goal is to produce a `paper.md` that is as close to the original published paper as possible.
>
> **Fidelity rules:**
>
> - **Preserve original numbering exactly.** Section numbers, equation numbers, table numbers, and figure numbers must match the original paper. Do not add, remove, or renumber anything.
> - **Preserve original prose exactly.** Do not paraphrase, summarize, or rewrite. Fix only OCR errors (e.g., `Universi@` → `University`, `clussiJier` → `classifier`). When fixing OCR errors, note them.
> - **Preserve original structure.** If the original has unnumbered subsections, keep them unnumbered (or match whatever the original does). Do not restructure.
>
> **MyST frontmatter:**
>
> ```yaml
> ---
> title: <exact title from paper>
> authors:
>   - name: <Author Name>
>     affiliation: <Affiliation as printed>
> date: <publication date, YYYY-MM-DD>
> venue: <journal name, volume, pages>
> bibliography: references.bib
> acknowledgments: <acknowledgments text if present>
> exports:
>   - format: typst
>     id: paper-pdf
> downloads:
>   - id: paper-pdf
>     title: Download PDF
> ---
> ```
>
> **Abstract:**
>
> ```markdown
> +++ {"part": "abstract"}
> <abstract text>
> +++
> ```
>
> **Sections:** Use MyST section labels for cross-referencing:
>
> ```markdown
> (sec-introduction)=
> ## 1. Introduction
> ```
>
> Label format: `(sec-<descriptive-slug>)=`
>
> **Equations:** Use `$$` math blocks with MyST labels matching original equation numbers:
>
> ```markdown
> $$
> \lambda_{at} = e_t(z_{at})
> $$ (eq-trade-decision)
> ```
>
> Reference equations with `{eq}\`eq-trade-decision\``.
>
> **Tables:** Use MyST `list-table` directive with `:name:` labels:
>
> ````markdown
> ```{list-table} Table 5b: Equilibrium holdings
> :header-rows: 1
> :name: tbl-economy-a1-equilibrium
>
> * - $i$
>   - $\pi_1^H(2)$
>   - $\pi_2^H(1)$
> * - 1
>   - 1
>   - 0.5
> ```
> ````
>
> Every table in the original paper must have a corresponding table in the output. Verify the count.
>
> **Figures:** Use MyST `figure` directive:
>
> ````markdown
> ```{figure} figures/fig1_classifier_flow.png
> :name: fig-classifier-flow
> :width: 80%
> :align: center
>
> Figure 1: Flow chart of the classifier system
> ```
> ````
>
> **Citations:** Create `references.bib` with all references. Use `{cite}\`key\`` in text:
>
> ```markdown
> {cite}`kiyotaki1989` studied how three classes...
> ```
>
> Citation keys: `authorYYYY` format (e.g., `kiyotaki1989`, `holland1975`).
>
> **Footnotes:** Use MyST footnote syntax:
>
> ```markdown
> ...classifier systems.[^fn1]
>
> [^fn1]: The way in which we model agents...
> ```
>
> Number footnotes sequentially matching the original: `[^fn1]`, `[^fn2]`, etc.
>
> **Cross-references:**
> - Sections: `{ref}\`sec-kw-environment\``
> - Equations: `{eq}\`eq-trade-decision\``
> - Tables: `{numref}\`tbl-economy-a1-equilibrium\``
> - Figures: `{numref}\`fig-classifier-flow\``
>
> **Definitions and theorems:** Use admonition-style blocks if the paper has formal definitions:
>
> ````markdown
> ```{admonition} Definition: Optimality
> A classifier system...
> ```
> ````

### Step 4: Section-by-section quality assessment

After the full conversion pass, verify each section against the original PDF. Work through the paper section by section:

1. **Open the original PDF** side-by-side with the generated `paper.md`
2. **For each section**, verify:
   - Prose matches word-for-word (aside from OCR corrections)
   - All equations are present and correctly typeset
   - All tables are present with correct numerical values
   - All figures are referenced
   - All footnotes are present
   - All citations use `{cite}` syntax and point to valid BibTeX keys
   - Cross-references use `{ref}`, `{eq}`, `{numref}` syntax

3. **Fix any discrepancies** — this is where most of the work happens. Common issues:
   - Tables with many sub-tables (e.g., "Table 6a–6k") are often partially extracted
   - Footnotes in later sections are frequently missed
   - Complex multi-line equations may be garbled
   - Dense numerical tables may have OCR errors in values

### Step 5: Build and verify

```bash
myst build
myst start
```

Open the rendered HTML and visually compare against the original PDF. Check:
- Equations render correctly (no broken LaTeX)
- Tables display with correct alignment and values
- Figures appear at appropriate locations
- Cross-references resolve (no broken links)
- Bibliography renders completely

---

## Quality Verification Checklist

After conversion, produce a fidelity report covering each of these areas. Target: **≥ 90% fidelity** overall.

### Structure
- [ ] All sections present with correct numbering
- [ ] All subsections present (numbered or unnumbered, matching original)
- [ ] Section labels defined for cross-referencing

### Equations
- [ ] Count matches original (list each: equation number → MyST label → status)
- [ ] LaTeX renders correctly in `myst build`
- [ ] Cross-references (`{eq}`) resolve

### Tables
- [ ] Count matches original (including sub-tables like 6a, 6b, ..., 6k)
- [ ] All numerical values spot-checked against original
- [ ] Table labels (`:name:`) defined for cross-referencing
- [ ] Table captions match original

### Figures
- [ ] Count matches original
- [ ] Images extracted or recreated at acceptable quality
- [ ] Figure labels (`:name:`) defined
- [ ] Figure captions match original

### Footnotes
- [ ] Count matches original
- [ ] Content matches original
- [ ] Numbered sequentially (`[^fn1]` through `[^fnN]`)

### Citations & References
- [ ] All in-text citations converted to `{cite}` syntax
- [ ] All entries present in `references.bib`
- [ ] No broken citation references in build output

### Prose Fidelity
- [ ] Sample 3–5 paragraphs from different sections and compare word-for-word
- [ ] OCR errors corrected (document any corrections made)
- [ ] Italics, bold, and emphasis match original

### MyST Build
- [ ] `myst build` completes without errors
- [ ] No unresolved cross-references
- [ ] HTML output renders correctly

---

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Missing tables in Section 7+ | `marker-pdf` often loses complex tables deep in papers | Manually transcribe from PDF, verify numerical values |
| Garbled equations | OCR misreads math symbols (e.g., `∑` → `E`, subscripts lost) | Compare each equation against PDF, rewrite LaTeX by hand |
| Missing footnotes | Footnotes in later pages often dropped by extraction | Scan PDF page-by-page for footnote markers |
| Broken citation keys | Inconsistent author-year in original (e.g., "Axelrod 1986" vs "1987") | Pick one and note the discrepancy |
| `list-table` formatting | Whitespace-sensitive — extra/missing spaces break rendering | Test each table individually with `myst build` |
| OCR of institution names | University names often garbled (e.g., `Universi@` for `University`) | Cross-check author block against known affiliations |
| Multi-column table layouts | Original PDF uses multi-column layouts that marker flattens | Reconstruct table structure from PDF visual layout |
| Duplicate `:name:` labels | Copy-paste errors when creating many similar tables | Use systematic naming: `tbl-economy-{id}-{content}` |

---

## Reference: MyST Syntax Quick Guide

```markdown
# Frontmatter
---
title: ...
authors: ...
bibliography: references.bib
---

# Abstract
+++ {"part": "abstract"}
Abstract text here.
+++

# Section with label
(sec-my-section)=
## 1. My Section Title

# Equation with label
$$
x = y + z
$$ (eq-my-equation)

# Inline math
The variable $x$ represents...

# Citation
{cite}`author1990`

# Cross-references
{ref}`sec-my-section`
{eq}`eq-my-equation`
{numref}`tbl-my-table`
{numref}`fig-my-figure`

# Footnote
Some text.[^fn1]
[^fn1]: Footnote content here.

# Figure
```{figure} figures/my_figure.png
:name: fig-my-figure
:width: 80%
Figure 1: Caption text
```

# Table
```{list-table} Table 1: Caption
:header-rows: 1
:name: tbl-my-table

* - Col A
  - Col B
* - val1
  - val2
```
```

---

## Lessons Learned

### From Marimon, McGrattan & Sargent (1990)
*45-page economics paper: 17 equations, 66 tables, 17 footnotes, 10 figures, 21 references.*

1. **`marker-pdf` gets you ~60–70% of the way.** The raw extraction captures prose well but frequently loses complex tables, later footnotes, and some equation formatting. Plan to spend significant effort on tables.

2. **Tables are the bottleneck.** This paper had ~50 sub-tables of simulation results. The initial extraction captured ~16. The remaining ~50 had to be manually transcribed from the PDF. Use systematic `:name:` labels (e.g., `tbl-economy-a11-holdings`) to stay organized.

3. **Section-by-section QA is essential.** A full-paper pass produces a good first draft, but section-by-section comparison against the PDF catches missing content — especially in results sections where tables and prose interleave densely.

4. **Footnotes in late sections get dropped.** This paper had 17 footnotes; the first pass captured only 10. Footnotes 11–17 (all in Section 7) had to be added manually.

5. **Numerical values must be spot-checked.** For tables with empirical results, verify 3–5 values per table against the PDF. OCR errors in digits (e.g., `0.502` vs `0.592`) are subtle and easy to miss.

6. **The quality assessment report is a deliverable.** Producing a structured fidelity report (like our `2026-02-16-pdf-to-myst-comparison.md`) forces thoroughness and creates an auditable record of conversion quality.

7. **`myst build` is your friend.** Build early and often. Broken LaTeX, unresolved cross-references, and malformed tables show up immediately in build output.

### From Sargent (1993) — Bounded Rationality in Macroeconomics
*204-page book (7 chapters): ~130 equations, 51 figures, 158 footnotes, 198 references, 0 tables.*

8. **Split long documents into per-chapter files.** A single 200+ page document overwhelms LLM context. Splitting into `ch01.md`–`ch07.md` made each chapter independently convertible and dramatically improved quality. This is the most important lesson for book-length works.

9. **Chapters can be converted in parallel.** With per-chapter files, independent chapters can be handed to subagents for simultaneous conversion, significantly reducing total wall-clock time.

10. **Book-length PDFs take ~60+ min with marker-pdf.** A 204-page book took ~64 minutes on macOS (CPU-bound; MPS not supported for the table detection model). Plan accordingly.

11. **marker-pdf occasionally misses the second figure from a page.** When two figures appear on the same PDF page, marker sometimes extracts only one. We saw 2 of 51 images missing. These need manual extraction from the source PDF.

12. **References are usually well-extracted.** The bibliography section is predominantly plain text and extracts cleanly. Converting ~200 entries to BibTeX is straightforward (and a good task for an LLM).

13. **`base_url` is needed for GitHub Pages.** Set `site.options.base_url: /<repo-name>` in `myst.yml`. The GitHub Actions workflow should also set `BASE_URL` as an environment variable.

14. **Chapter 5 (the core technical chapter) was by far the largest** at ~1,100 lines — as long as chapters 2, 3, 6, and 7 combined. Expect uneven chapter sizes; the most technical/mathematical chapters will require the most conversion effort.
