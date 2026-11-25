# Omer Nachmani

Personal engineering portfolio, research overview, and technical notes at [omernachmani.github.io](https://omernachmani.github.io).

The site covers electrical engineering, embedded systems and RTL design, hardware and application security, reverse engineering, and systems tooling. Current research and projects are separate from planned writeups. Every planned writeup entry is visibly marked **To be continued…**.

## Structure

| Location | Purpose |
| --- | --- |
| `content/pages/` | Homepage, background, research overview, project archive, and project detail pages |
| `content/writeups.json` | Writeup titles, categories, summaries, topics, and publication status |
| `templates/base.html` | Shared page metadata, navigation, and footer |
| `templates/writeup-content.html` | Starting outline for a technical writeup |
| `assets/css/main.css` | Monochrome typography, layouts, print styles, and code formatting |
| `assets/js/main.js` | Optional search and category filters for the writeup index |
| `tools/build.py` | Static HTML generator using the Python standard library |
| `index.html`, `about.html`, `research/`, `projects/`, `writeups/` | Generated pages served by GitHub Pages |

The site has no package dependencies, external fonts, tracking scripts, or JavaScript requirement for reading. Search and category filtering are progressive enhancements. The previous template's unused scripts, icon fonts, banner image, and Sass sources have been removed.

## Edit and preview

Use Python 3.9 or newer. Edit the source fragments, shared template, stylesheet, or writeup metadata, then regenerate the pages:

```bash
python3 tools/build.py
python3 -m http.server 8000
```

Open `http://localhost:8000`. A local server is needed because internal links start at the site root.

To verify that generated pages match the source:

```bash
python3 tools/build.py --check
```

To create a separate static preview directory:

```bash
python3 tools/build.py --output dist
```

## Add or complete a writeup

Add an entry to `content/writeups.json`, or edit an existing one. Supported categories are `reverse`, `hardware`, `application`, `embedded`, `systems`, and `lab`.

A planned entry uses `status: "planned"`, a short `summary`, a `scope` paragraph, a `topics` list, and search `tags`. Leave publication dates out of planned entries. The generator adds **To be continued…** to both the index and the individual page. These pages are marked `noindex` and excluded from the sitemap until published.

When the actual writeup is ready:

1. Copy `templates/writeup-content.html` to `content/writeups/<slug>.html`.
2. Replace the outline with the completed analysis. Keep useful heading IDs for the table of contents, and remove sections that do not apply.
3. In the matching JSON entry, set `status` to `published`, add the actual publication `date` in `YYYY-MM-DD` format, and set `body_file` to the fragment path, such as `content/writeups/<slug>.html`.
4. Run `python3 tools/build.py` and review the result.
5. Commit both the source and regenerated pages.

The builder requires a content file and a valid date before an entry can be published. Label a planned investigation as a finding only when the supporting work exists.

Use semantic HTML for article content: paragraphs, lists, tables with captions, and `<pre><code>` blocks. For a Hebrew passage, use `dir="rtl"` on its containing element; code blocks retain left-to-right direction. Use `<bdi>` when an inline identifier needs direction isolation.

## Design

The design uses white backgrounds, black and gray text, serif headings and prose, restrained sans-serif navigation, and monospace code. Layouts work on mobile, keyboard focus remains visible, and print styles retain the article content. There are no decorative icons or emoji.

## Deployment

GitHub Pages serves the repository root from `main`. The generated pages are committed, and `.nojekyll` keeps the site buildless on the hosting side. Rebuild after source changes before pushing to `main`.

`_config.yml` contains descriptive metadata only; it does not load a Jekyll theme. `.openai/` and `dist/` are ignored local preview state and are not needed for GitHub Pages.

## Attribution

The original version used the Strongly Typed template by [HTML5 UP](https://html5up.net/strongly-typed). Its attribution and Creative Commons Attribution 3.0 license remain in the footer and `LICENSE.txt`.
