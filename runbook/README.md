---
project: byronxlg
tier: 3
owner: byron
lifecycle: production
reviewed: 2026-09-22
---

# byronxlg runbook

The GitHub profile README at https://github.com/byronxlg. The projects block is rendered from the
fleet registry (`byronxlg/management` `projects.yaml`) by `bin/fleet page --push`, the same
command that renders https://byronxlg.com/, so the profile and the projects page always list the
same projects with the same text and posters. Tier 3: nothing runs continuously; if the operator
tick stops, the profile keeps rendering with a stale block and nothing is lost.

## Where it runs

Entirely on GitHub. The repo `byronxlg/byronxlg` is the deployment: whatever is on `main` is
what the profile shows. The renderer runs on the management host (`bin/tick`, launchd
`com.management.tick`, every 20 min) and pushes only `README.md`, only when the rendered block
differs. No workflow in this repo, no secret.

## What "live" means

The profile renders at https://github.com/byronxlg and the projects block matches the registry:
every live project with a `page:` block (except this one) appears, with a poster that loads.

## Objectives

| Indicator | Target | Window | Measured by |
| --- | --- | --- | --- |
| The block matches the registry | every weekly review | 7 days | `bin/fleet page /tmp/p` in management, `diff <(sed -n '/projects:start/,/projects:end/p' README.md) ...` or just read both |
| Poster images load (camo proxies them; a 404 shows a broken image) | every weekly review | 7 days | open the profile; `curl -I` each `img src` |

Recovery targets (from `projects.yaml`): detect 7 d, restore 14 d. RPO n/a; the block is
regenerated from the registry and nothing is stored here.

## Who is watching

Nothing off-host, by design for tier 3. The weekly fleet review in `management` (`bin/fleet
check`) is the only watcher.

## Files

| Question | File |
| --- | --- |
| How does a change land, how do I roll back? | [updates.md](updates.md) |

## Schedules

| What | Where it runs | When | Notes |
| --- | --- | --- | --- |
| `bin/fleet page --push`: render the page and this README's block, push each if changed | management tick (launchd) | every 20 min | A tick with nothing changed pushes nothing; the push log is `git log --format=%s README.md` |

## History

- 2026-07: profile README with `scripts/update_projects.py` and a daily workflow listing every
  public repo and three hand-picked cards.
- 2026-09-22: consolidated with byronxlg.com (management D35): the workflow, script and SVG
  cards removed; the block is rendered from the registry.
