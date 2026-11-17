<div align="center">

# mohammadi.cv

[![CV](https://github.com/mohammadi-hadi/mohammadi-hadi.github.io/actions/workflows/cv.yml/badge.svg)](https://github.com/mohammadi-hadi/mohammadi-hadi.github.io/actions/workflows/cv.yml)
[![Scholar](https://github.com/mohammadi-hadi/mohammadi-hadi.github.io/actions/workflows/scholar.yml/badge.svg)](https://github.com/mohammadi-hadi/mohammadi-hadi.github.io/actions/workflows/scholar.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Personal academic website of Hadi Mohammadi, researcher in explainable NLP at Utrecht University (PhD 2026) and Senior AI & Data Science Expert - R&D Specialist at AcademicTransfer.*

</div>

Live at https://mohammadi.cv (served by GitHub Pages with a custom domain).

## Overview

A static HTML/CSS/JavaScript site with pages for research, publications, projects, experience, news, and CV. No build system is required for the pages themselves; the repository is published as-is (`.nojekyll`).

Two GitHub Actions workflows keep the content fresh:

- `.github/workflows/cv.yml` — rebuilds the CV PDF with [RenderCV](https://github.com/rendercv/rendercv) whenever `cv/Hadi_Mohammadi_CV.yaml` changes.
- `.github/workflows/scholar.yml` — refreshes the Google Scholar figures in `assets/data/scholar.json` with `scripts/fetch_scholar.py`. Scholar blocks GitHub's runners, so the daily run happens on a Mac and this workflow is kept for manual runs.

## Local development

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```
