# byronxlg

GitHub profile README for https://github.com/byronxlg. `main` is what the profile shows. The
block between `<!-- projects:start -->` and `<!-- projects:end -->` in `README.md` is generated:
`bin/fleet page --push` in `byronxlg/management` renders it from the fleet registry
(`projects.yaml`, the same source as https://byronxlg.com/) every operator tick and pushes it
here when it changed. Do not edit the block by hand; change the `page:` block of the project in
the registry instead. Everything above the markers is hand-written and changes through a PR.

Operational docs live in `runbook/`:

- [runbook/README.md](runbook/README.md): what this is, what "live" means, who renders it.
- [runbook/updates.md](runbook/updates.md): how a change lands, rollback, risky changes.
