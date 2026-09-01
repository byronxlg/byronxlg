---
project: byronxlg
tier: 3
owner: byron
lifecycle: production
reviewed: 2026-09-01
---

# byronxlg runbook

The GitHub profile README at https://github.com/byronxlg. A scheduled GitHub Actions workflow
regenerates the projects section (three featured cards plus a table of every public repo) from
the GitHub API and commits the result. Tier 3: nothing runs continuously; if the workflow stops,
the profile keeps rendering with a stale project list and nothing is lost.

## Where it runs

Entirely on GitHub. The repo `byronxlg/byronxlg` is the deployment: whatever is on `main` is
what the profile shows. The only moving part is `.github/workflows/update-projects.yml`, which
runs `scripts/update_projects.py` on an `ubuntu-latest` runner with the job's own `GITHUB_TOKEN`.
No host, no container, no secret outside GitHub.

## What "live" means

The profile renders at https://github.com/byronxlg and the project list is fresh: every public
non-fork repo appears in the table, and the featured cards in `assets/cards/` match the repos in
the script's `FEATURED` list.

## Objectives

| Indicator | Target | Window | Measured by |
| --- | --- | --- | --- |
| `update-projects.yml` has a completed run within 2x its cadence (48 h) and the latest run concluded `success` | every weekly review | 7 days | `gh run list --repo byronxlg/byronxlg --workflow update-projects.yml --limit 1` |

Recovery targets (from `projects.yaml`): detect 7 d, restore 14 d. RPO n/a; the section is
regenerated from the API and nothing is stored.

A run that finds nothing to change makes no commit, so the bot commit history is not the
freshness signal. The run history is.

## Who is watching

Nothing off-host, by design for tier 3. The weekly fleet review in `management` (`bin/fleet
check`, then the run-history query above) is the only watcher. GitHub also emails the repo owner
when a scheduled workflow run fails.

## Files

| Question | File |
| --- | --- |
| How is the README generated, how do I run it by hand, how do I roll back? | [updates.md](updates.md) |

## Schedules

| What | Where it runs | When | Notes |
| --- | --- | --- | --- |
| `update-projects.yml`: run `scripts/update_projects.py byronxlg`, commit `README.md` and `assets/cards/` if changed | github-actions | `0 18 * * *` (06:00 NZST, 07:00 NZDT); also on push to `main` and `workflow_dispatch` | Refreshes the projects table (repo list, order, descriptions, languages, homepage links) and the three featured SVG cards. GitHub delays on-the-hour crons: observed starts range from 18:30 UTC to the small hours of the next day |

## Dashboards and logs

- Run history: https://github.com/byronxlg/byronxlg/actions/workflows/update-projects.yml
- `gh run list --repo byronxlg/byronxlg --workflow update-projects.yml --limit 10`
- Bot commits: `git log --author='github-actions' --oneline` in the checkout.
