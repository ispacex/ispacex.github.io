# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jekyll static site for the Inner Space Exploration Institute — an educational content repository focused on cultural preservation (dance, theatre, yoga, art history, traditional knowledge systems). Hosted on GitHub Pages at `ispacex.github.io`.

Primary content language is Russian with English references.

## Build & Development

```bash
# Serve locally (requires Ruby + Bundler)
bundle exec jekyll serve
# Site at http://localhost:4000
```

No Gemfile is tracked — the site relies on GitHub Pages' built-in Jekyll with the `dracula/gh-pages` remote theme configured in `_config.yml`.

Deployment is automatic: push to `main` triggers a GitHub Pages build.

## Architecture

**Jekyll static site** using Liquid templates and Markdown content.

- `_config.yml` — Jekyll config (remote theme, Google Analytics)
- `_layouts/` — Page layout templates (e.g., `donate.html`)
- `_includes/` — Reusable Liquid components:
  - `head.html` — HTML head with GA tracking
  - `youtube.html`, `instagram.html` — Media embed helpers
  - `copy.html`, `copy_erc20.html`, `copy_trc20.html` — Clipboard copy components for crypto donation addresses
- `styles/css/style.scss` — Main stylesheet using SCSS with CSS custom properties, dark theme (`#0f1115` background), imports Minima classic skin

**Content directories** are flat Markdown collections organized by topic: `art/`, `dance/`, `theatre/`, `ksh/`, `nt/`, `hoop/`, `yoga/`, `books/`. Each has an `index.md` entry point.

The `dance/` directory contains Natya Shastra chapter translations (`ns-ch1.md` through `ns-ch14.md`, `ns-ch37.md`).

## Key Conventions

- Content pages are Markdown with Jekyll front matter
- Embed external media using the `youtube.html` and `instagram.html` includes
- Donation pages use the `donate` layout with crypto address copy components

## Ship (Marchaj Book) — S3 Integration

The `ship/` directory hosts the digitized book "Теория плавания под парусами" by Czesław Marchaj.

**Large files (PDF, DjVu) are stored on S3**, not in the git repo:
- S3 bucket: `theatre-th`, prefix: `ship/`
- Public URL: `https://theatre-th.s3.amazonaws.com/ship/theory.pdf`
- CORS is configured for `https://ispacex.github.io`

**To update the PDF after rebuilding:**
1. Build in the markhai repo: `cd ~/git/misc/books/markhai && make`
2. Upload to S3: `./scripts/upload_to_s3.sh` (reads `.credentials` file)
3. No need to commit/push anything to ispacex for PDF changes

**To update ship/ HTML pages** (viewers, dictionary, formulas, etc.):
1. Edit files in `~/git/ispacex/ship/`
2. Commit and push to `main` — GitHub Pages auto-deploys

S3 credentials are in `~/git/misc/books/markhai/.credentials` (gitignored).

## Git Conventions

**Write commit messages in English** — subject line and body alike, even though the
site content is Russian. Existing Russian commits stay as they are; new ones are English.
