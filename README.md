# nomad-hpc.com

The website of [NØMAÐ](https://github.com/jtonini/nomad-hpc), open-source monitoring and diagnostics for HPC clusters. One page, built with [Hugo](https://gohugo.io/) (0.142 or later).

```bash
hugo server            # preview at http://localhost:1313
hugo --gc --minify     # build into public/
```

## Where things are

| What | Where |
|---|---|
| Version, links, contact, the Console's repository | `hugo.toml` (`[params]`) |
| The page itself | `layouts/_default/index.html` |
| The Console tour (tabs, pages, captions) | `data/tour.yaml` |
| The paper's BibTeX | `data/citation.yaml` |
| The wordmark (drawn as SVG) | `layouts/partials/wordmark.html` |
| The "How it fits together" diagram | `layouts/partials/architecture.html` |
| Styles and the little script | `assets/css/style.css`, `assets/js/site.js` (served under names that change with their contents) |
| Screenshots and art | `static/images/` |

The version line reads the latest release from PyPI when the page loads; `version` and `released` in `hugo.toml` are what it shows when PyPI can't be reached, so update them now and then. When the Console's repository is public, put its address in `console_repo` and the Get started section links to it; until then it describes the Console without a link.

The page names no institution: screenshots come from `nomad demo`'s made-up people and cluster, and the footer's Contact link appears only when `contact` is set.

## Screenshots

`scripts/make_screenshots.py` takes them all again from the demo: the Console's pages as a student, a PI and an admin, the phone view, `nomad edu explain`, and the weekly email. Its first lines say what it needs. Make the demo (the seed keeps the job numbers the script uses):

```bash
nomad demo --console ~/nomad-site-demo --seed 2
```

Start the Console on it, in the Console's backend folder, in another terminal:

```bash
HOME=~/nomad-site-demo NOMAD_CONSOLE_DEMO=1 python3 -m uvicorn app.main:app --port 8000
```

Then, in this repository:

```bash
python3 scripts/make_screenshots.py ~/nomad-site-demo
```

`static/images/og.jpg` (the preview when the link is shared) and `hero-network.webp` (the hero's background, the top of the original art) are made by hand.

## License

The site's own code is under the Apache License 2.0 (`LICENSE`). NØMAÐ itself is under the GNU AGPL v3.0.
