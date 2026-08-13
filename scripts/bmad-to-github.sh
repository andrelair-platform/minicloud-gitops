#!/usr/bin/env bash
# bmad-to-github.sh — push BMAD story files to GitHub Issues
#
# Usage:
#   ./scripts/bmad-to-github.sh <story-dir> [--repo <org/repo>] [--project <number>] [--dry-run]
#
# Example:
#   ./scripts/bmad-to-github.sh bmad/stories/cert-1/m1-m2 \
#     --repo andrelair-platform/platform-backlog \
#     --project 2 \
#     --milestone "CERT-1 M1-M2 — ktayl-policy-service (Go)"
#
# Requirements: gh CLI authenticated, python3 in PATH

set -euo pipefail

STORY_DIR=""
REPO="andrelair-platform/platform-backlog"
PROJECT_NUMBER="2"
MILESTONE_TITLE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo) REPO="$2"; shift 2 ;;
    --project) PROJECT_NUMBER="$2"; shift 2 ;;
    --milestone) MILESTONE_TITLE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) STORY_DIR="$1"; shift ;;
  esac
done

if [[ -z "$STORY_DIR" ]]; then
  echo "Error: story directory required" >&2
  echo "Usage: $0 <story-dir> [--repo org/repo] [--project N] [--milestone 'title'] [--dry-run]" >&2
  exit 1
fi

if [[ ! -d "$STORY_DIR" ]]; then
  echo "Error: directory not found: $STORY_DIR" >&2
  exit 1
fi

# Parse YAML frontmatter from a story file using python3
parse_frontmatter() {
  local file="$1"
  python3 - "$file" <<'PYEOF'
import sys, re

with open(sys.argv[1]) as f:
    content = f.read()

# Extract YAML block between first two --- lines
m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
if not m:
    sys.exit(1)

yaml_block = m.group(1)
body = content[m.end():]

# Simple key: value parser (handles quoted strings and lists)
def parse_yaml(text):
    result = {}
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        # Key: value or Key: [list] (inline)
        km = re.match(r'^(\w[\w/]*)\s*:\s*(.*)', line)
        if km:
            key = km.group(1)
            val = km.group(2).strip()
            # Inline list [a, b, c]
            if val.startswith('['):
                items = re.findall(r'[\w\-/.: ]+', val[1:val.rfind(']')])
                result[key] = [x.strip() for x in items if x.strip()]
            elif val.startswith('"') or val.startswith("'"):
                result[key] = val.strip('"\'')
            elif val == '':
                # Multiline list
                sub_items = []
                i += 1
                while i < len(lines) and lines[i].startswith('  - '):
                    sub_items.append(lines[i].strip()[2:])
                    i += 1
                result[key] = sub_items
                continue
            else:
                result[key] = val
        i += 1
    return result

meta = parse_yaml(yaml_block)

# Extract story body (first ## section content as description)
# Use the full body as the issue body
print(f"TITLE={meta.get('title', '')}")
print(f"ESTIMATE={meta.get('estimate', '')}")
print(f"PRIORITY={meta.get('priority', '')}")
labels = meta.get('labels', [])
if isinstance(labels, list):
    print(f"LABELS={','.join(labels)}")
else:
    print(f"LABELS={labels}")
print(f"STORY_ID={meta.get('id', '')}")

# Write body to stdout after a separator
print("---BODY---")
print(body.strip())
PYEOF
}

# Resolve milestone number from title
get_milestone_number() {
  local title="$1"
  gh api "repos/${REPO}/milestones" --jq ".[] | select(.title == \"$title\") | .number" 2>/dev/null | head -1
}

echo "==> Scanning stories in: $STORY_DIR"
echo "==> Repo: $REPO"
echo "==> Project: #$PROJECT_NUMBER"
[[ -n "$MILESTONE_TITLE" ]] && echo "==> Milestone: $MILESTONE_TITLE"
[[ "$DRY_RUN" == true ]] && echo "==> DRY RUN — no issues will be created"
echo ""

MILESTONE_NUMBER=""
if [[ -n "$MILESTONE_TITLE" ]]; then
  MILESTONE_NUMBER=$(get_milestone_number "$MILESTONE_TITLE")
  if [[ -z "$MILESTONE_NUMBER" ]]; then
    echo "Warning: milestone '$MILESTONE_TITLE' not found in $REPO — issues will be created without milestone" >&2
  else
    echo "==> Milestone #$MILESTONE_NUMBER found"
  fi
fi

created=0
skipped=0

for story_file in "$STORY_DIR"/S*.md; do
  [[ -f "$story_file" ]] || continue

  # Parse frontmatter
  parsed=$(parse_frontmatter "$story_file") || {
    echo "  [SKIP] $story_file — could not parse frontmatter"
    ((skipped++))
    continue
  }

  # Extract fields
  TITLE=$(echo "$parsed" | grep '^TITLE=' | cut -d= -f2-)
  LABELS=$(echo "$parsed" | grep '^LABELS=' | cut -d= -f2-)
  STORY_ID=$(echo "$parsed" | grep '^STORY_ID=' | cut -d= -f2-)
  ESTIMATE=$(echo "$parsed" | grep '^ESTIMATE=' | cut -d= -f2-)

  # Extract body (everything after ---BODY---)
  BODY=$(echo "$parsed" | awk '/^---BODY---/{found=1; next} found{print}')

  # Append estimate to body footer
  BODY="${BODY}

---
**Estimate:** ${ESTIMATE} story points | **BMAD ID:** ${STORY_ID}"

  echo "  [STORY] $STORY_ID — $TITLE"
  echo "          Labels: $LABELS | Estimate: $ESTIMATE sp"

  if [[ "$DRY_RUN" == true ]]; then
    echo "          [DRY RUN] Would create issue"
    ((created++))
    continue
  fi

  # Check if issue already exists (by BMAD ID in title search)
  existing=$(gh issue list --repo "$REPO" --search "$STORY_ID in:title" --json number,title --jq '.[0].number' 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    echo "          [SKIP] Issue #$existing already exists"
    ((skipped++))
    continue
  fi

  # Build gh issue create args
  gh_args=(
    issue create
    --repo "$REPO"
    --title "$TITLE"
    --body "$BODY"
  )

  # Add labels (comma-separated)
  if [[ -n "$LABELS" ]]; then
    IFS=',' read -ra label_arr <<< "$LABELS"
    for label in "${label_arr[@]}"; do
      label=$(echo "$label" | xargs)  # trim whitespace
      gh_args+=(--label "$label")
    done
  fi

  # Add milestone
  if [[ -n "$MILESTONE_NUMBER" ]]; then
    gh_args+=(--milestone "$MILESTONE_NUMBER")
  fi

  issue_url=$(gh "${gh_args[@]}" 2>&1)
  issue_number=$(echo "$issue_url" | grep -oE '[0-9]+$' || true)

  if [[ -n "$issue_number" ]]; then
    echo "          Created: $issue_url"

    # Add to project board
    if [[ -n "$PROJECT_NUMBER" ]]; then
      gh project item-add "$PROJECT_NUMBER" \
        --owner "$(echo "$REPO" | cut -d/ -f1)" \
        --url "$issue_url" 2>/dev/null && echo "          Added to project #$PROJECT_NUMBER" || \
        echo "          Warning: could not add to project #$PROJECT_NUMBER"
    fi
    ((created++))
  else
    echo "          Error creating issue: $issue_url" >&2
  fi

  # Small delay to avoid rate limiting
  sleep 1
done

echo ""
echo "==> Done. Created: $created | Skipped: $skipped"
