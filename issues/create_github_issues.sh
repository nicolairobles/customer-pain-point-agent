#!/usr/bin/env bash
set -euo pipefail

# Map work-breakdown owner labels to GitHub usernames.
# Always update this mapping when team membership changes so issues get assigned correctly.
owner_to_handles() {
  case "$1" in
    "Nicolai") echo "nicolairobles" ;;
    "Javier") echo "JavierZavaleta94" ;; # TODO: replace with Javier's GitHub handle (e.g., javier-example)
    "Stefan") echo "sndez" ;; # TODO: replace with Stefan's GitHub handle
    "Edison") echo "" ;; # TODO: replace with Edison's GitHub handle
    "Amanda") echo "polskapanda" ;; # TODO: replace with Amanda's GitHub handle
    "Al") echo "alemieux3" ;; # TODO: replace with Al's GitHub handle
    "Javier, Stefan, Edison") echo "JavierZavaleta94 sndez edisonake" ;; # TODO: optionally assign multiple handles separated by spaces
    "All team members (parallel)") echo "nicolairobles JavierZavaleta94 sndez edisonake polskapanda’ alemieux3" ;; # Leave blank to skip assignment for shared ownership
    *) echo "" ;; # Default: no assignment for unrecognized owner labels
  esac
}

# Abort early if the GitHub CLI is not available; assignments require authenticated gh access.
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install it from https://cli.github.com/" >&2
  exit 1
fi

MODE="create"
TARGET_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --update)
      MODE="update"
      shift
      ;;
    *)
      TARGET_ID="$1"
      shift
      ;;
  esac
done

files=()
while IFS= read -r file; do
  files+=("$file")
done < <(find issues/generated -type f -name '*.md' | sort)

for issue_file in "${files[@]}"; do
  basename="$(basename "$issue_file")"

  # Skip files that do not match the requested activity ID (when supplied).
  if [[ -n "$TARGET_ID" && "$basename" != "$TARGET_ID"* ]]; then
    continue
  fi

  # Extract issue title from the first markdown heading in the generated file.
  title_line=$(head -n 1 "$issue_file")
  title=${title_line#\# }

  # Extract the owners from the summary section to look up GitHub assignees.
  owner_line=$(grep -m1 -E '^- \*\*Owner\(s\):\*\*' "$issue_file" || true)
  owner_label=${owner_line#- **Owner(s):** }
  handles=$(owner_to_handles "$owner_label")

  # Build assignment arguments for gh CLI; only add flags when we have known handles.
  assign_args=()
  if [[ -n "$handles" ]]; then
    for handle in $handles; do
      if [[ "$MODE" == "update" ]]; then
      # Validate that the GitHub username exists before attempting assignment (no effect if empty).
      if [[ -n "$handle" ]] && gh api "users/$handle" > /dev/null 2>&1; then
        assign_args+=(--add-assignee "$handle")
      fi
      else
      if [[ -n "$handle" ]] && gh api "users/$handle" > /dev/null 2>&1; then
        assign_args+=(--assignee "$handle")
      fi
      fi
    done
  fi

  # Look for an existing issue with the same title to prevent duplicates.
  existing_number=$(gh issue list --search "in:title \"$title\"" --limit 1 --json number --jq '.[0].number' 2>/dev/null || true)

  if [[ -n "$existing_number" ]]; then
    if [[ "$MODE" == "update" ]]; then
      echo "Updating issue #$existing_number: $title"
      if [[ ${#assign_args[@]} -gt 0 ]]; then
        if ! gh issue edit "$existing_number" --body-file "$issue_file" "${assign_args[@]}"; then
          echo "Warning: assignment update failed for issue #$existing_number; updating body only." >&2
          gh issue edit "$existing_number" --body-file "$issue_file"
        fi
      else
        gh issue edit "$existing_number" --body-file "$issue_file"
      fi
    else
      echo "Skipping existing issue #$existing_number: $title"
    fi
    continue
  fi

  if [[ "$MODE" == "update" ]]; then
    echo "No existing issue found for $title; skipping update."
    continue
  fi

  echo "Creating issue: $title"
  if [[ ${#assign_args[@]} -gt 0 ]]; then
    if ! gh issue create --title "$title" --body-file "$issue_file" "${assign_args[@]}"; then
      echo "Warning: assignment failed; creating issue without assignees." >&2
      gh issue create --title "$title" --body-file "$issue_file"
    fi
  else
    gh issue create --title "$title" --body-file "$issue_file"
  fi
done


# ./issues/create_github_issues.sh 1.1.4 → creates the issue only if it doesn’t already exist.
# ./issues/create_github_issues.sh --update 1.1.4 → replaces the issue body if it already exists (skips if it doesn’t).