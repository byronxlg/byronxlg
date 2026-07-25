#!/usr/bin/env python3
"""Regenerates the projects section of README.md and the SVG repo cards.

Rewrites everything between the <!-- projects:start --> / <!-- projects:end -->
markers: cards for the repos in FEATURED (in that order), then a collapsible
table of all public non-fork repos. Cards are rendered locally so the profile
has no dependency on third-party image services. A card embeds its preview
image when assets/previews/<name>.jpg exists; otherwise it renders text-only.
"""

import base64
import json
import pathlib
import subprocess
import sys
import textwrap
from urllib.parse import urlparse
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "assets" / "cards"
PREVIEWS_DIR = ROOT / "assets" / "previews"
README = ROOT / "README.md"

# Hand-picked showcase, in display order. A listed repo that the public API
# does not return (private, deleted, renamed) is skipped, so a repo made
# public later appears on the next regeneration without a code change.
FEATURED = ["skillfold", "polymarket-tui", "semantic-similarity", "dotfiles"]

# Showcase entries without a public repo: the card links to the live product
# and the details are stated here, since the API cannot supply them. The
# repo behind semantic-similarity is intentionally private.
EXTERNAL_FEATURED = {
    "semantic-similarity": {
        "name": "semantic-similarity",
        "html_url": "https://semanticsimilarity.byronxlg.com/",
        "description": "Compare two texts by meaning: embeddings and cosine "
        "similarity, with saved comparison history",
        "language": "JavaScript",
        "stargazers_count": None,
    }
}

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
}
DEFAULT_LANGUAGE_COLOR = "#8b949e"

# Single mid-tone palette with a transparent background: GitHub's theme
# setting and the viewer's OS color scheme can disagree, and an SVG served
# through camo only sees the OS scheme, so theme-adaptive colors would
# mismatch the page for some viewers. Neutral colors read on both grounds.
CARD_STYLE = """  <style>
    .bg { fill: none; stroke: #7d8590; stroke-opacity: 0.4; }
    .name { fill: #4184e4; font: 600 14px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
    .desc, .meta { fill: #7d8590; font: 400 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
  </style>"""

TEXT_CARD = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120" viewBox="0 0 400 120" role="img" aria-label="{name}">
{style}
  <rect class="bg" x="0.5" y="0.5" width="399" height="119" rx="6"/>
  <text class="name" x="16" y="30">{name}</text>
  <text class="desc" x="16" y="54">{desc_line1}<tspan x="16" dy="17">{desc_line2}</tspan></text>
  <circle cx="21" cy="94" r="5" fill="{lang_color}"/>
  <text class="meta" x="33" y="98">{language}</text>
  <text class="meta" x="150" y="98">{meta_right}</text>
</svg>
"""

IMAGE_CARD = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="352" viewBox="0 0 400 352" role="img" aria-label="{name}">
{style}
  <rect class="bg" x="0.5" y="0.5" width="399" height="351" rx="6"/>
  <clipPath id="preview"><rect x="12" y="12" width="376" height="227" rx="4"/></clipPath>
  <image href="data:image/jpeg;base64,{preview}" x="12" y="12" width="376" height="227" preserveAspectRatio="xMidYMid slice" clip-path="url(#preview)"/>
  <text class="name" x="16" y="266">{name}</text>
  <text class="desc" x="16" y="289">{desc_line1}<tspan x="16" dy="17">{desc_line2}</tspan></text>
  <circle cx="21" cy="327" r="5" fill="{lang_color}"/>
  <text class="meta" x="33" y="331">{language}</text>
  <text class="meta" x="150" y="331">{meta_right}</text>
</svg>
"""


def fetch_repos(user):
    out = subprocess.run(
        ["gh", "api", f"users/{user}/repos?per_page=100&type=owner"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        r
        for r in json.loads(out)
        if not r["fork"] and not r["archived"] and r["name"] != user
    ]


def sort_repos(repos):
    repos = sorted(repos, key=lambda r: r["pushed_at"] or "", reverse=True)
    return sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)


def render_card(repo):
    lines = textwrap.wrap(repo["description"] or "", width=56)
    line1 = lines[0] if lines else ""
    line2 = (
        textwrap.shorten(" ".join(lines[1:]), width=56, placeholder="...")
        if len(lines) > 1
        else ""
    )
    language = repo["language"] or "-"
    fields = {
        "style": CARD_STYLE,
        "name": escape(repo["name"]),
        "desc_line1": escape(line1),
        "desc_line2": escape(line2),
        "language": escape(language),
        "lang_color": LANGUAGE_COLORS.get(language, DEFAULT_LANGUAGE_COLOR),
        "meta_right": (
            f"&#9733; {repo['stargazers_count']}"
            if repo["stargazers_count"] is not None
            else escape(urlparse(repo["html_url"]).netloc)
        ),
    }
    preview = PREVIEWS_DIR / f"{repo['name']}.jpg"
    if preview.exists():
        fields["preview"] = base64.b64encode(preview.read_bytes()).decode()
        return IMAGE_CARD.format(**fields)
    return TEXT_CARD.format(**fields)


def table_row(repo):
    name = f"[{repo['name']}]({repo['html_url']})"
    if repo.get("homepage"):
        name += f" ([site]({repo['homepage']}))"
    description = (repo["description"] or "").replace("|", "\\|")
    return f"| {name} | {description} | {repo['language'] or '-'} | {repo['stargazers_count']} |"


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else "byronxlg"
    repos = sort_repos(fetch_repos(user))
    by_name = {r["name"]: r for r in repos}
    by_name.update(EXTERNAL_FEATURED)
    top = [by_name[n] for n in FEATURED if n in by_name]

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    wanted = {f"{r['name']}.svg" for r in top}
    for stale in CARDS_DIR.glob("*.svg"):
        if stale.name not in wanted:
            stale.unlink()
    for repo in top:
        (CARDS_DIR / f"{repo['name']}.svg").write_text(render_card(repo))

    cards = "\n".join(
        f'<a href="{r["html_url"]}"><img src="assets/cards/{r["name"]}.svg" alt="{r["name"]}" width="400"></a>'
        for r in top
    )
    table = "\n".join(
        ["| Project | Description | Language | Stars |", "| --- | --- | --- | --- |"]
        + [table_row(r) for r in repos]
    )
    section = (
        f"{cards}\n\n<details>\n<summary>All public projects</summary>\n\n{table}\n\n</details>"
    )

    content = README.read_text()
    start = "<!-- projects:start -->"
    end = "<!-- projects:end -->"
    head, _, rest = content.partition(start)
    _, _, tail = rest.partition(end)
    README.write_text(f"{head}{start}\n{section}\n{end}{tail}")


if __name__ == "__main__":
    main()
