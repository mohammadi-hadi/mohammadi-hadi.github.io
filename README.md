# mohammadi.cv

Personal academic website of Hadi Mohammadi — PhD researcher in Explainable NLP at Utrecht University.

Live at https://mohammadi.cv (served by GitHub Pages with a custom domain).

## Overview

A static HTML/CSS/JavaScript site (based on a Bootstrap template) with pages for research, publications, projects, experience, news, and CV. No build system is required for the pages themselves; the repository is published as-is (`.nojekyll`).

Two GitHub Actions workflows keep the content fresh:

- `.github/workflows/cv.yml` — rebuilds the CV PDF with [RenderCV](https://github.com/rendercv/rendercv) whenever `cv/Hadi_Mohammadi_CV.yaml` changes.
- `.github/workflows/scholar.yml` — a daily job that refreshes publication and profile data (Google Scholar, GitHub, ORCID, OpenAlex) via the scripts in `scripts/`.

## Local development

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

See `local_testing_guide.md` for more detail.
