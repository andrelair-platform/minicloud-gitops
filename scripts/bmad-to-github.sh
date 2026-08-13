#!/usr/bin/env bash
# bmad-to-github.sh — push BMAD story files to GitHub Issues
#
# Usage:
#   ./scripts/bmad-to-github.sh <story-dir> [options]
#
# Options:
#   --repo <org/repo>       target repo (default: andrelair-platform/platform-backlog)
#   --project <number>      GitHub Project number (default: 1 = minicloud platform roadmap)
#   --milestone <title>     GitHub Milestone title to attach issues to
#   --dry-run               print what would happen, create nothing
#
# Example:
#   ./scripts/bmad-to-github.sh bmad/stories/cert-1/m1-m2 \
#     --milestone "CERT-1 M1-M2 — ktayl-policy-service (Go)"
#
# Idempotent: issues already containing [S001-slug] in their title are skipped.
# Requirements: gh CLI authenticated, python3 in PATH

set -euo pipefail

STORY_DIR=""
REPO="andrelair-platform/platform-backlog"
PROJECT_NUMBER="1"
MILESTONE_TITLE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo)      REPO="$2";             shift 2 ;;
    --project)   PROJECT_NUMBER="$2";   shift 2 ;;
    --milestone) MILESTONE_TITLE="$2";  shift 2 ;;
    --dry-run)   DRY_RUN=true;          shift   ;;
    *)           STORY_DIR="$1";        shift   ;;
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

# ---------------------------------------------------------------------------
# Parse YAML frontmatter from a story file
# ---------------------------------------------------------------------------
parse_frontmatter() {
  local file="$1"
  python3 - "$file" <<'PYEOF'
import sys, re

with open(sys.argv[1]) as f:
    content = f.read()

m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
if not m:
    sys.exit(1)

yaml_block = m.group(1)
body = content[m.end():]

def parse_yaml(text):
    result = {}
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        km = re.match(r'^(\w[\w/]*)\s*:\s*(.*)', line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            if val.startswith('['):
                items = re.findall(r'[\w\-/.: ]+', val[1:val.rfind(']')])
                result[key] = [x.strip() for x in items if x.strip()]
            elif val.startswith('"') or val.startswith("'"):
                result[key] = val.strip('"\'')
            elif val == '':
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

story_id = meta.get('id', '')
raw_title = meta.get('title', '')
# Always prefix title with [story-id] for idempotent deduplication
prefixed_title = f"[{story_id}] {raw_title}" if story_id else raw_title

labels = meta.get('labels', [])
if isinstance(labels, list):
    labels_str = ','.join(labels)
else:
    labels_str = str(labels)

print(f"TITLE={prefixed_title}")
print(f"ESTIMATE={meta.get('estimate', '')}")
print(f"LABELS={labels_str}")
print(f"STORY_ID={story_id}")
print("---BODY---")
print(body.strip())
PYEOF
}

# ---------------------------------------------------------------------------
# Auto-create any missing labels on the target repo
# ---------------------------------------------------------------------------
ensure_labels() {
  local labels_csv="$1"
  IFS=',' read -ra arr <<< "$labels_csv"
  for label in "${arr[@]}"; do
    label=$(echo "$label" | xargs)
    [[ -z "$label" ]] && continue
    # gh label create is idempotent-ish: exits 0 if label already exists
    gh label create "$label" \
      --color "6b7280" \
      --description "BMAD label" \
      --repo "$REPO" 2>/dev/null || true
  done
}

# ---------------------------------------------------------------------------
echo "==> Scanning: $STORY_DIR"
echo "==> Repo:     $REPO"
echo "==> Project:  #$PROJECT_NUMBER"
[[ -n "$MILESTONE_TITLE" ]] && echo "==> Milestone: $MILESTONE_TITLE"
[[ "$DRY_RUN" == true ]]    && echo "==> DRY RUN — no issues will be created"
echo ""

# Verify milestone exists
if [[ -n "$MILESTONE_TITLE" ]]; then
  ms_number=$(gh api "repos/${REPO}/milestones" \
    --jq ".[] | select(.title == \"$MILESTONE_TITLE\") | .number" 2>/dev/null | head -1)
  if [[ -z "$ms_number" ]]; then
    echo "Warning: milestone '$MILESTONE_TITLE' not found — issues will be created without one" >&2
    MILESTONE_TITLE=""
  else
    echo "==> Milestone #$ms_number found"
  fi
fi

created=0
skipped=0

for story_file in "$STORY_DIR"/S*.md; do
  [[ -f "$story_file" ]] || continue

  parsed=$(parse_frontmatter "$story_file") || {
    echo "  [SKIP] $story_file — could not parse frontmatter"
    skipped=$((skipped + 1))
    continue
  }

  TITLE=$(echo    "$parsed" | grep '^TITLE='    | cut -d= -f2-)
  LABELS=$(echo   "$parsed" | grep '^LABELS='   | cut -d= -f2-)
  STORY_ID=$(echo "$parsed" | grep '^STORY_ID=' | cut -d= -f2-)
  ESTIMATE=$(echo "$parsed" | grep '^ESTIMATE=' | cut -d= -f2-)
  BODY=$(echo     "$parsed" | awk '/^---BODY---/{found=1; next} found{print}')

  BODY="${BODY}

---
**Estimate:** ${ESTIMATE} story points | **BMAD ID:** \`${STORY_ID}\`"

  echo "  [STORY] $STORY_ID"
  echo "          Title:  $TITLE"
  echo "          Labels: $LABELS | ${ESTIMATE}sp"

  if [[ "$DRY_RUN" == true ]]; then
    echo "          [DRY RUN] Would create issue"
    created=$((created + 1))
    continue
  fi

  # Idempotency check — search for [STORY_ID] prefix in title
  existing=$(gh issue list \
    --repo "$REPO" \
    --search "[${STORY_ID}] in:title" \
    --json number \
    --jq '.[0].number' 2>/dev/null || true)

  if [[ -n "$existing" ]]; then
    echo "          [SKIP] Already exists as #$existing"
    skipped=$((skipped + 1))
    continue
  fi

  # Ensure all labels exist before trying to attach them
  ensure_labels "$LABELS"

  # Build gh issue create args
  gh_args=(issue create --repo "$REPO" --title "$TITLE" --body "$BODY")

  IFS=',' read -ra label_arr <<< "$LABELS"
  for label in "${label_arr[@]}"; do
    label=$(echo "$label" | xargs)
    [[ -n "$label" ]] && gh_args+=(--label "$label")
  done

  [[ -n "$MILESTONE_TITLE" ]] && gh_args+=(--milestone "$MILESTONE_TITLE")

  issue_url=$(gh "${gh_args[@]}" 2>&1) || {
    echo "          Error: $issue_url" >&2
    continue
  }

  echo "          Created: $issue_url"

  # Add to project board (non-fatal if it fails)
  if [[ -n "$PROJECT_NUMBER" ]]; then
    gh project item-add "$PROJECT_NUMBER" \
      --owner "$(cut -d/ -f1 <<< "$REPO")" \
      --url "$issue_url" 2>/dev/null \
      && echo "          Added to project #$PROJECT_NUMBER" \
      || echo "          Warning: project add failed (non-fatal)"
  fi

  created=$((created + 1))
  sleep 1
done

echo ""
echo "==> Done. Created: $created | Skipped (already exist): $skipped"
