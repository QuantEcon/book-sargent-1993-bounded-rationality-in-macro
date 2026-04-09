# Bounded Rationality in Macroeconomics

**Thomas J. Sargent (1993)**

## About

This repository contains:

1. A **MyST Markdown version** of the book, converted from the [original PDF](source/Sargent_1993_Bounded_Rationality_in_Macroeconomics.pdf)
2. Companion resources and lectures (in progress)

> Sargent, T. J. (1993). *Bounded Rationality in Macroeconomics*. Oxford University Press.

## Project Structure

```
├── paper/                      # MyST paper source
│   ├── paper.md                # Full paper in MyST Markdown
│   ├── figures/                # Paper figures
│   └── references.bib          # Bibliography
├── source/                     # Original source materials
│   └── *.pdf                   # Original paper PDF
├── _archive/                   # Construction & intermediate files
│   └── marker_output/          # Raw marker-pdf extraction
├── pyproject.toml              # Python project config (uv)
├── uv.lock                     # Dependency lockfile
├── myst.yml                    # MyST site configuration
└── .gitignore
```

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [MyST](https://mystmd.org/) (`npm install -g mystmd`)

### Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create repo-level virtual environment and install all dependencies
uv sync
```

This creates a `.venv/` inside the repo with all dependencies (numpy, matplotlib, marker-pdf, etc.) isolated from other projects.

### Running commands

```bash
# Run any command in the repo environment
uv run python script.py
uv run marker_single source/input.pdf --output_dir _archive/marker_output/

# Or activate the environment directly
source .venv/bin/activate
```

### Build MyST site

```bash
myst build
myst start
```

## Conversion Workflow

See [PROMPT-PDF-TO-MD.md](PROMPT-PDF-TO-MD.md) for the PDF → MyST conversion process.
