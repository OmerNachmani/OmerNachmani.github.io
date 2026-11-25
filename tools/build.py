#!/usr/bin/env python3
"""Build the static portfolio using only Python's standard library."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import date
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://omernachmani.github.io"
PENDING = "To be continued…"
CATEGORIES = {
    "reverse": "Reverse engineering",
    "hardware": "Embedded & hardware security",
    "application": "Application security",
    "embedded": "Embedded systems & RTL",
    "systems": "Systems & tooling",
    "lab": "CTFs & lab notes",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(template: str, values: dict[str, str]) -> str:
    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Missing template value: {key}")
        return values[key]
    return re.sub(r"@@([a-z_]+)@@", substitute, template)


def asset_version(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]


def page(title: str, description: str, route: str, body: str, active: str, indexable: bool = True) -> str:
    links = [
        ("Overview", "/", "home"),
        ("Research", "/research/", "research"),
        ("Projects", "/projects/", "projects"),
        ("Writeups", "/writeups/", "writeups"),
        ("About", "/about.html", "about"),
    ]
    navigation = "\n        ".join(
        f'<a href="{href}"' + (' aria-current="page"' if key == active else '') + f'>{label}</a>'
        for label, href, key in links
    )
    return render((ROOT / "templates/base.html").read_text(encoding="utf-8"), {
        "title": esc(title + " | Omer Nachmani"), "description": esc(description),
        "canonical": esc(ORIGIN + route),
        "robots": '<meta name="robots" content="index, follow">' if indexable else '<meta name="robots" content="noindex, follow">',
        "navigation": navigation, "body": body.rstrip(),
        "css_version": asset_version("assets/css/main.css"),
        "js_version": asset_version("assets/js/main.js"),
    })


def load_writeups() -> list[dict]:
    entries = json.loads((ROOT / "content/writeups.json").read_text(encoding="utf-8"))
    seen = set()
    for entry in entries:
        slug = entry.get("slug", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in seen:
            raise ValueError(f"Invalid or duplicate writeup slug: {slug}")
        seen.add(slug)
        if entry.get("category") not in CATEGORIES:
            raise ValueError(f"Unknown category for {slug}")
        for field in ("title", "summary"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f"Missing {field} for {slug}")
        if entry.get("status") not in {"planned", "published"}:
            raise ValueError(f"Unknown publication status for {slug}")
        if entry["status"] == "planned":
            if entry.get("date"):
                raise ValueError(f"A planned entry must not have a publication date: {slug}")
            if not entry.get("scope") or not entry.get("topics"):
                raise ValueError(f"Planned entry needs scope and topics: {slug}")
        else:
            date.fromisoformat(entry["date"])
            source = (ROOT / entry["body_file"]).resolve()
            if not source.is_relative_to(ROOT / "content") or not source.is_file():
                raise ValueError(f"Published body must be a file under content/: {slug}")
            if not source.read_text(encoding="utf-8").strip():
                raise ValueError(f"Published entry has an empty body: {slug}")
    return entries


def writeup_route(entry: dict) -> str:
    return "/writeups/" + entry["slug"] + ".html"


def publication_label(entry: dict) -> str:
    if entry["status"] == "planned":
        return f'<p class="entry-status">{PENDING}</p>'
    day = date.fromisoformat(entry["date"])
    return f'<p class="entry-meta"><time datetime="{day.isoformat()}">{day.strftime("%d %B %Y")}</time></p>'


def writeup_index(entries: list[dict]) -> str:
    buttons = '<button type="button" data-filter="all" aria-pressed="true">All topics</button>\n'
    buttons += "\n".join(f'<button type="button" data-filter="{key}" aria-pressed="false">{esc(label)}</button>' for key, label in CATEGORIES.items())
    rows = []
    for entry in entries:
        category = CATEGORIES[entry["category"]]
        terms = " ".join([entry["title"], entry["summary"], entry.get("scope", ""), category,
                          *entry.get("tags", []), *entry.get("topics", [])])
        rows.append(f'''<li class="entry" data-entry data-categories="{esc(entry['category'])}" data-search="{esc(terms)}">
          <p class="entry-meta">{esc(category)}</p>
          <h2 class="entry-title"><a href="{writeup_route(entry)}">{esc(entry['title'])}</a></h2>
          <p class="entry-summary">{esc(entry['summary'])}</p>
          {publication_label(entry)}
          <p class="entry-topics">{esc(' · '.join(entry.get('tags', [])[:6]))}</p>
        </li>''')
    return f'''    <header class="page-intro">
      <p class="eyebrow">Technical writing</p><h1>Writeups</h1>
      <p class="lead">Reverse engineering, embedded and hardware security, application security, RTL design, embedded systems, and engineering tooling.</p>
    </header>
    <div class="writing-controls" hidden>
      <div><label for="writeup-search">Search topics and tools</label><input id="writeup-search" type="search" placeholder="For example: firmware, RISC-V, Verilog, GDB, UART" autocomplete="off" aria-controls="writeup-list"></div>
      <div class="filter-group" role="group" aria-label="Filter writeups by area">{buttons}</div>
      <p id="filter-count" role="status" aria-live="polite" aria-atomic="true"></p>
    </div>
    <ul class="entry-list" id="writeup-list">{''.join(rows)}</ul>
    <div id="no-results" hidden><h2>No matching entries</h2><p>Try a different term or return to all topics.</p><button type="button" data-reset>Clear search and filters</button></div>
'''


def writeup_body(entry: dict) -> str:
    related = ""
    if entry.get("related"):
        related = '<section id="related"><h2>Related work</h2><ul>' + ''.join(
            f'<li><a href="{esc(item["href"])}">{esc(item["label"])}</a></li>' for item in entry["related"]
        ) + '</ul></section>'
    if entry["status"] == "planned":
        contents = '<section id="scope"><h2>Planned scope</h2><p>' + esc(entry["scope"]) + '</p></section>'
        contents += '<section id="topics"><h2>Topics to cover</h2><ul>' + ''.join(f'<li>{esc(topic)}</li>' for topic in entry["topics"]) + '</ul></section>' + related
        toc = '<li><a href="#scope">Planned scope</a></li><li><a href="#topics">Topics to cover</a></li>'
        if related:
            toc += '<li><a href="#related">Related work</a></li>'
    else:
        contents = (ROOT / entry["body_file"]).read_text(encoding="utf-8") + related
        headings = re.findall(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', contents, re.DOTALL)
        toc = ''.join(f'<li><a href="#{esc(anchor)}">{esc(re.sub("<[^>]+>", "", text))}</a></li>' for anchor, text in headings)
        if not toc:
            toc = '<li><a href="#article-body">Read the writeup</a></li>'
    return f'''    <nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/writeups/">Writeups</a><span aria-hidden="true"> / </span><span>{esc(CATEGORIES[entry['category']])}</span></nav>
    <header class="article-header">
      <p class="eyebrow">{esc(CATEGORIES[entry['category']])}</p><h1>{esc(entry['title'])}</h1>
      <p class="lead">{esc(entry['summary'])}</p>{publication_label(entry)}
    </header>
    <div class="article-layout">
      <article class="prose" id="article-body">{contents}<p><a href="/writeups/?category={entry['category']}">Back to this research area</a></p></article>
      <aside class="toc" aria-labelledby="contents-title"><h2 id="contents-title">On this page</h2><nav aria-label="Article contents"><ol>{toc}</ol></nav></aside>
    </div>
'''


def build() -> dict[str, str]:
    output = {}
    pages = [
        ("index.html", "/", "home", "home", "Hardware, embedded systems, and security", "Omer Nachmani's portfolio: electrical engineering, embedded systems, RTL design, RISC-V power side-channel research, and technical writeups."),
        ("research/index.html", "/research/", "research", "research", "Research", "Ongoing hardware security research by Omer Nachmani, including power side-channel attacks on a RISC-V processor implemented on FPGA."),
        ("projects/index.html", "/projects/", "projects", "projects", "Projects", "Engineering and security projects by Omer Nachmani across embedded systems, microcontrollers, timing side channels, and developer tools."),
        ("about.html", "/about.html", "about", "about", "About", "Omer Nachmani — electrical engineer with experience in Intel system validation, Wi-Fi firmware and driver debugging, embedded systems, and independent security research."),
        ("research/riscv-side-channel.html", "/research/riscv-side-channel.html", "riscv-side-channel", "research", "Power side-channel attack on RISC-V", "A project overview of software AES-128 on PicoRV32, the CW305 and Husky platform, baseline key recovery, and hardware countermeasure research."),
        ("projects/timing-side-channel.html", "/projects/timing-side-channel.html", "timing-side-channel", "projects", "A timing side-channel demonstration", "SimpleTimingSCA: an educational Arduino and Python demonstration of timing leakage from an early-exit PIN comparison."),
    ]
    indexable_routes = []
    for destination, route, source, active, title, description in pages:
        body = (ROOT / f"content/pages/{source}.html").read_text(encoding="utf-8")
        output[destination] = page(title, description, route, body, active)
        indexable_routes.append(route)
    entries = load_writeups()
    output["writeups/index.html"] = page("Writeups", "Technical writeups on reverse engineering, embedded and hardware security, application security, RTL design, embedded systems, systems tooling, and lab notes.", "/writeups/", writeup_index(entries), "writeups")
    indexable_routes.append("/writeups/")
    for entry in entries:
        route = writeup_route(entry)
        is_published = entry["status"] == "published"
        output[route.lstrip("/")] = page(entry["title"], entry["summary"], route, writeup_body(entry), "writeups", is_published)
        if is_published:
            indexable_routes.append(route)
    not_found = '''    <header class="page-intro"><p class="eyebrow">404</p><h1>Page not found</h1><p class="lead">The page may have moved, or the address may be incomplete.</p><p>Return to the <a href="/">overview</a>, browse the <a href="/projects/">project archive</a>, visit <a href="/research/">research</a>, or open the <a href="/writeups/">writeup index</a>.</p></header>'''
    output["404.html"] = page("Page not found", "The requested page could not be found.", "/404.html", not_found, "", False)
    output["sitemap.xml"] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{esc(ORIGIN + route)}</loc></url>\n' for route in indexable_routes) + '</urlset>\n'
    output["robots.txt"] = "User-agent: *\nDisallow: /content/\nDisallow: /templates/\nDisallow: /tools/\nSitemap: " + ORIGIN + "/sitemap.xml\n"
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT, help="Output directory; defaults to repository root")
    parser.add_argument("--check", action="store_true", help="Check generated pages match the source")
    args = parser.parse_args()
    destination = args.output.resolve()
    output = build()
    mismatches = []
    for relative, content in output.items():
        path = destination / relative
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if mismatches:
        print("Generated files need rebuilding:\n" + "\n".join(mismatches), file=sys.stderr)
        return 1
    if not args.check and destination != ROOT:
        for relative in ["assets/css/main.css", "assets/js/main.js", "LICENSE.txt", ".nojekyll"]:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
    print(f"{'Verified' if args.check else 'Built'} {len(output)} files in {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
