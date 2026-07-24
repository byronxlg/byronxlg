#!/usr/bin/env bash
# Regenerates the projects table in README.md between the
# <!-- projects:start --> and <!-- projects:end --> markers.
set -euo pipefail

user="${1:-byronxlg}"
readme="$(cd "$(dirname "$0")/.." && pwd)/README.md"

table="$(gh api "users/${user}/repos?per_page=100&type=owner" --jq '
  [ .[]
    | select(.fork == false and .archived == false)
    | select(.name != "'"${user}"'")
  ]
  | sort_by([.stargazers_count, .pushed_at]) | reverse
  | map(
      "| [\(.name)](\(.html_url))"
      + (if (.homepage // "") != "" then " ([site](\(.homepage)))" else "" end)
      + " | \((.description // "") | gsub("\\|"; "\\\\|"))"
      + " | \(.language // "-")"
      + " | \(.stargazers_count) |"
    )
  | ["| Project | Description | Language | Stars |", "| --- | --- | --- | --- |"] + .
  | join("\n")
')"

table="$table" awk '
  /<!-- projects:start -->/ { print; print ENVIRON["table"]; skip = 1; next }
  /<!-- projects:end -->/ { skip = 0 }
  !skip { print }
' "$readme" > "${readme}.tmp"
mv "${readme}.tmp" "$readme"
