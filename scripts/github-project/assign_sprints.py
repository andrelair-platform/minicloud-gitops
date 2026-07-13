#!/usr/bin/env python3
"""Assign Sprint iterations to all project items based on milestone and status.

Usage: python3 assign_sprints.py
Requires: gh CLI authenticated as org owner

Sprint mapping (update SPRINTS dict if iterations are regenerated):
  Sprint 1: Jul 14 – Jul 27   (Done + active items + v2 AI milestone)
  Sprint 2: Jul 28 – Aug 10   (v3 Insurance Ops + no-milestone backlog)
  Sprint 3: Aug 11 – Aug 24   (v4 Data Platform + no-milestone backlog)
  Sprint 4: Aug 25 – Sep 07   (v5 Enterprise Expansion early)
  Sprint 5: Sep 08 – Sep 21   (v5 Enterprise Expansion mid)
  Sprint 6: Sep 22 – Oct 05   (v5 Enterprise Expansion late)
"""
import subprocess, json, time
from collections import Counter

ORG = "andrelair-platform"
REPO = "platform-backlog"
PROJECT_NUM = 1
PROJECT_ID = "PVT_kwDOEN4i9s4BbQIF"
SPRINT_FIELD_ID = "PVTIF_lADOEN4i9s4BbQIFzhXy__c"

SPRINTS = {
    1: "bb392d41",  # Jul 14 – Jul 27
    2: "d984a07e",  # Jul 28 – Aug 10
    3: "c3683cd7",  # Aug 11 – Aug 24
    4: "06b714bd",  # Aug 25 – Sep 07
    5: "591b05e0",  # Sep 08 – Sep 21
    6: "b452bd65",  # Sep 22 – Oct 05
}

def gh(query):
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True)
    return json.loads(r.stdout)

# ── Step 1: Get all project items ─────────────────────────────────────────────
print("── Fetching project items ───────────────────────────────────────────")
items = []
cursor = None
while True:
    after = f', after: "{cursor}"' if cursor else ""
    data = gh(f"""{{
      organization(login: "{ORG}") {{
        projectV2(number: {PROJECT_NUM}) {{
          items(first: 100{after}) {{
            pageInfo {{ hasNextPage endCursor }}
            nodes {{
              id
              content {{
                ... on Issue {{ number }}
              }}
              status: fieldValueByName(name: "Status") {{
                ... on ProjectV2ItemFieldSingleSelectValue {{ name }}
              }}
            }}
          }}
        }}
      }}
    }}""")
    page = data["data"]["organization"]["projectV2"]["items"]
    items.extend(page["nodes"])
    if not page["pageInfo"]["hasNextPage"]:
        break
    cursor = page["pageInfo"]["endCursor"]

print(f"  ✓ {len(items)} items fetched")

# ── Step 2: Get milestone assignments from GitHub issues API ──────────────────
print("── Fetching issue milestones ─────────────────────────────────────────")
issue_milestone = {}
page_num = 1
while True:
    r = subprocess.run(
        ["gh", "api", f"repos/{ORG}/{REPO}/issues?state=all&per_page=100&page={page_num}"],
        capture_output=True, text=True
    )
    batch = json.loads(r.stdout)
    if not batch:
        break
    for iss in batch:
        num = iss["number"]
        m = iss.get("milestone")
        issue_milestone[num] = m["number"] if m else None
    if len(batch) < 100:
        break
    page_num += 1

print(f"  ✓ {len(issue_milestone)} issues with milestone data")
ms_counts = Counter(v for v in issue_milestone.values())
print(f"    Milestone distribution: {dict(ms_counts)}")

# ── Step 3: Sprint assignment logic ──────────────────────────────────────────
no_ms_counter = 0

def assign_sprint(item):
    global no_ms_counter
    sv = item.get("status") or {}
    status = sv.get("name", "Backlog")
    content = item.get("content") or {}
    num = content.get("number")

    if status == "Done":
        return 1
    if status in ("In Progress", "This Sprint", "Blocked", "In Review"):
        return 1

    ms = issue_milestone.get(num) if num else None
    if ms == 1:   # v2 AI Platform
        return 1
    elif ms == 2: # v3 Insurance Ops
        return 2
    elif ms == 3: # v4 Data Platform
        return 3
    elif ms == 4: # v5 Enterprise Expansion — spread 4-6 by issue number
        if num and num <= 99:
            return 4
        elif num and num <= 119:
            return 5
        else:
            return 6
    else:
        # No milestone — spread across sprints 2-4
        no_ms_counter += 1
        return (no_ms_counter % 3) + 2

# ── Step 4: Preview ───────────────────────────────────────────────────────────
sprint_counts = Counter()
for item in items:
    sprint_counts[assign_sprint(item)] += 1
no_ms_counter = 0  # reset for actual run

print(f"\n── Sprint assignment preview ─────────────────────────────────────────")
for s in range(1, 7):
    print(f"  Sprint {s}: {sprint_counts[s]} issues")

# ── Step 5: Apply ─────────────────────────────────────────────────────────────
print(f"\n── Assigning sprints to {len(items)} items ──────────────────────────")
ok = 0
errors = 0

for i, item in enumerate(items):
    item_id = item["id"]
    sprint_num = assign_sprint(item)
    iteration_id = SPRINTS[sprint_num]

    r = subprocess.run([
        "gh", "api", "graphql",
        "-f", f"""query=mutation {{
  updateProjectV2ItemFieldValue(input: {{
    projectId: "{PROJECT_ID}"
    itemId: "{item_id}"
    fieldId: "{SPRINT_FIELD_ID}"
    value: {{ iterationId: "{iteration_id}" }}
  }}) {{ projectV2Item {{ id }} }}
}}"""
    ], capture_output=True, text=True)

    result = json.loads(r.stdout)
    if "errors" in result:
        print(f"  ✗ item {item_id}: {result['errors'][0]['message'][:80]}")
        errors += 1
    else:
        ok += 1

    if (i + 1) % 20 == 0:
        print(f"  Processed {i+1}/{len(items)}...")
    time.sleep(0.05)

print(f"\n  ✓ {ok} assigned, {errors} errors")
print(f"\n  Roadmap: https://github.com/orgs/{ORG}/projects/{PROJECT_NUM}/views/3")
