---
project: byronxlg
reviewed: 2026-09-22
deploy_path: push-to-main
rollback_minutes: 5
---

# Updates

`main` is production: GitHub renders the profile from the README on the default branch, so a
merge is a deploy and there is nothing to build or restart.

## How a change reaches production

| Change to | Pipeline | Trigger | Lands in prod when | Evidence |
| --- | --- | --- | --- | --- |
| Hand-written README content (bio, skills, links), `CLAUDE.md`, `runbook/` | PR, merge to `main` | merge | on merge | profile page |
| The projects block | `bin/fleet page --push` in `byronxlg/management` | every operator tick (20 min), or by hand | the tick pushes `README.md` when the rendered block differs | `git log --format='%h %s' README.md` shows "Update projects block from the fleet registry" |
| A project's blurb, site, poster, or whether it is listed | the project's `page:` block in management `projects.yaml` | commit there | next tick | same |

## Running it by hand

```sh
cd ~/repos/management && bin/fleet page --push
```

Preview without pushing: `bin/fleet page /tmp/p` writes `profile-block.md` next to the page.

## Rollback

`git revert <sha> && git push` on `main`, or restore an older `README.md`. The next tick
re-renders the block from the registry; if the revert was of a block change, fix the registry
first or the tick puts it back.

## Risky changes

- Removing a marker line: the renderer skips the file (logs "markers missing") and the block
  goes stale silently. Keep both markers.
- An untracked file in `~/repos/byronxlg`: never committed (the renderer adds only `README.md`),
  but keep the checkout on `main` and clean so the push is a fast-forward.
- The block's poster URLs point at each project's site or at byronxlg.com `assets/<name>/`;
  a project that loses its video shows text only, not a broken image.
