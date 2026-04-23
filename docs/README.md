# Project Website (GitHub Pages)

This directory is the source for the project's GitHub Pages site, served at:

```
https://adamxiaorose.github.io/Massive-Data-Project2/
```

## Deployment

1. In the GitHub repository, go to **Settings → Pages**.
2. Under **Build and deployment → Source**, select **Deploy from a branch**.
3. Under **Branch**, select `main` and folder `/docs`, then **Save**.
4. Wait ~1–2 minutes for the first build. Subsequent pushes to `main` rebuild automatically.

## Local preview

Requires Ruby (3.0+) and Bundler.

```bash
cd docs
bundle install
bundle exec jekyll serve --livereload
# → http://127.0.0.1:4000
```

## Structure

```
docs/
├── _config.yml              # Site configuration and navigation
├── _layouts/                # Page templates (default, page, home)
├── _includes/               # head, header, footer partials
├── assets/
│   ├── css/style.css        # Custom theme
│   └── figures/             # Eight PNG figures from outputs/figures
├── index.html               # Overview / landing page
├── findings.md              # Layer 2 + Layer 3 results
├── methodology.md           # Pipeline, modeling, reproducibility
├── proposal.md              # Phase 2 grant proposal
├── team.md                  # Authors and acknowledgements
├── 404.html
├── Gemfile                  # Pinned to the github-pages gem
└── README.md                # This file
```

## Content ownership

All research content (text, figures, methodology) was produced by Xiao Xu and Cassie Zhang for PPOL 5204 at Georgetown McCourt. The theme is custom — no external Jekyll theme is used.
