---
project: byronxlg
reviewed: 2026-09-01
deploy_path: push-to-main
rollback_minutes: 5
---

# Updates

`main` is production: GitHub renders the profile from the README on the default branch, so a
merge is a deploy and there is nothing to build or restart. Hand-written content (bio, skills,
the `FEATURED` list, preview images) changes through a PR. The block between
`<!-- projects:start -->` and `<!-- projects:end -->` is generated and is not edited by hand; the
next run overwrites it.

## How the README is generated

`scripts/update_projects.py <owner>` (Python 3 standard library plus the `gh` CLI):

1. Calls `gh api users/<owner>/repos?per_page=100&type=owner` and drops forks, archived repos
   and the profile repo itself. Sorts by stars, then by `pushed_at`.
2. For each name in `FEATURED` (`skillfold`, `polymarket-tui`, `semantic-similarity`) renders
   `assets/cards/<name>.svg`. A card embeds `assets/previews/<name>.jpg` as base64 when the file
   exists, otherwise it is text only. `EXTERNAL_FEATURED` supplies the details for
   `semantic-similarity`, whose repo is private. Cards for names no longer in `FEATURED` are
   deleted.
3. Rewrites the block between the markers: the card links, then the "All public projects" table
   (name, homepage link if set, description, language badge, live shields.io star badge).

Inputs: the public GitHub API, the two constants in the script, `assets/previews/`, and the
existing `README.md` (everything outside the markers is preserved). Outputs: `README.md` and
`assets/cards/*.svg`.

The workflow (`.github/workflows/update-projects.yml`) then runs `git add README.md assets/cards`
and, only if the staged diff is non-empty, commits as `github-actions[bot]` with the message
`Update projects section` and pushes to `main`. No diff, no commit: a green run with no commit is
normal and is most days.

## How a change reaches production

| Change to | Pipeline | Trigger | Lands in prod when | Evidence |
| --- | --- | --- | --- | --- |
| Hand-written README content, `assets/previews/`, `scripts/`, the workflow | PR, merge to `main` | merge | on merge; the push also runs `update-projects.yml`, which regenerates the section with the new code | profile page; the run after the merge |
| Projects section, `assets/cards/` | `update-projects.yml` | cron `0 18 * * *`, push to `main`, `workflow_dispatch` | the bot commit is pushed | `git log --author=github-actions`; run log |
| Another repo made public, renamed, described, or given a homepage | none needed | next scheduled run | within a day plus GitHub's cron delay | table row in `README.md` |

## Running it by hand

Trigger the workflow (preferred; identical to the cron path, commits if anything changed):

```sh
gh workflow run update-projects.yml --repo byronxlg/byronxlg
gh run watch --repo byronxlg/byronxlg
```

Locally, to preview the diff before a PR (needs `gh` authenticated; the script only reads from
the API):

```sh
cd ~/repos/byronxlg
python3 scripts/update_projects.py byronxlg
git diff --stat
```

A local run writes `README.md` and `assets/cards/`; commit them or discard with
`git checkout -- README.md assets/cards`.

## Post-deploy smoke test

Open https://github.com/byronxlg. The three cards render (an SVG, not a broken image), the
table lists every public repo, and
`gh run list --repo byronxlg/byronxlg --workflow update-projects.yml --limit 1` shows the
post-merge run as `success`. A broken card usually means an unescaped character in a
description; the templates escape through `xml.sax.saxutils`, so look for a change to the SVG
templates first.

## Rollback

Revert the offending commit on `main` and push; the profile updates as soon as the push lands.

- A bad bot commit: `git revert <sha>` of the `Update projects section` commit. The next run
  regenerates the same output unless the cause (a script or workflow change, or upstream repo
  metadata) is also fixed, so revert the code change in the same PR.
- A bad hand edit: revert the PR's merge commit.

Nothing else to roll back: no deployed artifact, no state.

## Scheduled maintenance

| What | Cadence | How | Validated by |
| --- | --- | --- | --- |
| `actions/checkout` (currently `v4`) | on a new major, or a deprecation notice in the run log | PR | the run after merge is green |
| Runner image `ubuntu-latest` and its `python3` / `gh` | none; follows GitHub | none | run log |
| `FEATURED` list and `assets/previews/*.jpg` | when the showcase should change | PR | cards render on the profile |
| `reviewed:` in this directory | 90 days | re-read, bump the date | `bin/fleet check` in management |

No dependabot config exists. Add `.github/dependabot.yml` for `github-actions` if manual
tracking lapses.

## Things that are risky to change

- **Token scope.** The workflow uses the job's `GITHUB_TOKEN` with `permissions: contents:
  write`, scoped to this repo, and reads only the public `users/<owner>/repos` endpoint. Do not
  swap in a PAT: a PAT-pushed commit fires the `push` event and the workflow would loop, and it
  widens the blast radius from one public repo to the account. Pushes made with `GITHUB_TOKEN`
  do not trigger workflows, which is what prevents the loop today.
- **The `push: main` trigger plus `contents: write`.** Every merge runs the script and may
  commit on top of `main`. Pull before pushing a follow-up, and keep the workflow's `git add`
  limited to `README.md` and `assets/cards`.
- **The markers.** The script uses `str.partition` on them. With the start marker missing it
  appends a second copy of the section; with the end marker missing it drops everything after
  the start marker. Keep both markers on their own lines.
- **Schedule silently disabled.** GitHub disables scheduled workflows in public repos after 60
  days without repository activity. Bot commits have kept it alive so far; if the list stops
  changing for two months the weekly review is what notices. `gh workflow view
  update-projects.yml --repo byronxlg/byronxlg` shows the state.
