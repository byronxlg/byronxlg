#!/usr/bin/env python3
"""Regenerates the projects section of README.md and the SVG repo cards.

Rewrites everything between the <!-- projects:start --> / <!-- projects:end -->
markers: card images for the top repos by stars, then a collapsible table of
all public non-fork repos. Cards are rendered locally so the profile has no
dependency on third-party image services.
"""

import json
import pathlib
import subprocess
import sys
import textwrap
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "assets" / "cards"
README = ROOT / "README.md"
TOP_N = 6

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
CARD_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120" viewBox="0 0 400 120" role="img" aria-label="{name}">
  <style>
    .bg {{ fill: none; stroke: #7d8590; stroke-opacity: 0.4; }}
    .name {{ fill: #4184e4; font: 600 14px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }}
    .desc, .meta {{ fill: #7d8590; font: 400 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }}
  </style>
  <rect class="bg" x="0.5" y="0.5" width="399" height="119" rx="6"/>
  <text class="name" x="16" y="30">{name}</text>
  <text class="desc" x="16" y="54">{desc_line1}<tspan x="16" dy="17">{desc_line2}</tspan></text>
  <circle cx="21" cy="94" r="5" fill="{lang_color}"/>
  <text class="meta" x="33" y="98">{language}</text>
  <text class="meta" x="150" y="98">&#9733; {stars}</text>
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


def card_worthy(repo):
    """Supporting repos don't belong on the cards even when they outrank
    real projects on stars: taps and dotfiles are infrastructure, and a
    repo without a description isn't being presented to anyone."""
    if repo["name"].startswith("homebrew-") or repo["name"] == "dotfiles":
        return False
    return bool(repo["description"])


def render_card(repo):
    lines = textwrap.wrap(repo["description"] or "", width=56)
    line1 = lines[0] if lines else ""
    line2 = (
        textwrap.shorten(" ".join(lines[1:]), width=56, placeholder="...")
        if len(lines) > 1
        else ""
    )
    language = repo["language"] or "-"
    return CARD_TEMPLATE.format(
        name=escape(repo["name"]),
        desc_line1=escape(line1),
        desc_line2=escape(line2),
        language=escape(language),
        lang_color=LANGUAGE_COLORS.get(language, DEFAULT_LANGUAGE_COLOR),
        stars=repo["stargazers_count"],
    )


def table_row(repo):
    name = f"[{repo['name']}]({repo['html_url']})"
    if repo.get("homepage"):
        name += f" ([site]({repo['homepage']}))"
    description = (repo["description"] or "").replace("|", "\\|")
    return f"| {name} | {description} | {repo['language'] or '-'} | {repo['stargazers_count']} |"


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else "byronxlg"
    repos = sort_repos(fetch_repos(user))
    top = [r for r in repos if card_worthy(r)][:TOP_N]

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
