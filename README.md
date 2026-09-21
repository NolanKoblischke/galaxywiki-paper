# GalaxyWiki

This repository contains the paper’s data, prompts, evaluations, and prebuilt website.

Run `uv run reproduce.py` from this directory to rebuild coordinate groups and summarize saved results in `outputs/`. Python 3.13 or newer is required. The first run downloads dependencies; no model calls or credentials are needed.

Run `uv run --no-project python -m http.server 8000` and open <http://localhost:8000/site/> to browse GalaxyWiki.

Tables are in `data/`, prompts are in `prompts/`, and evaluation records are in `evaluation/`. Source attribution and font licenses remain bundled. Extraction and evaluation are not rerun.
