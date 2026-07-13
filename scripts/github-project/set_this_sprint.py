#!/usr/bin/env python3
"""Set Status='This Sprint' for all Sprint 1 items currently in Backlog.

Usage: python3 set_this_sprint.py
Requires: gh CLI authenticated as org owner

Run this at the start of each sprint to promote backlog items assigned
to the current sprint into the 'This Sprint' status column.
Update SPRINT1_ITERATION_ID to the active sprint's iteration ID.
"""
import subprocess, json, time

ORG = "andrelair-platform"
PROJECT_NUM = 1
PROJECT_ID = "PVT_kwDOEN4i9s4BbQIF"
STATUS_FIELD_ID = "PVTSSF_lADOEN4i9s4BbQIFzhWB8R4"
THIS_SPRINT_OPTION_ID = "26e76715"
SPRINT1_ITERATION_ID = "bb392d41"  # Sprint 1: Jul 14 – Jul 27

def gh(query):
    r = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True)
    return json.loads(r.stdout)

# Fetch all items with Sprint and Status values
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
              content {{ ... on Issue {{ number title }} }}
              status: fieldValueByName(name: "Status") {{
                ... on ProjectV2ItemFieldSingleSelectValue {{ name }}
              }}
              sprint: fieldValueByName(name: "Sprint") {{
                ... on ProjectV2ItemFieldIterationValue {{ iterationId title }}
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

# Filter: Sprint 1 items still in Backlog
sprint1_backlog = []
sprint1_all = []
for item in items:
    sprint = item.get("sprint") or {}
    if sprint.get("iterationId") == SPRINT1_ITERATION_ID:
        sprint1_all.append(item)
        if (item.get("status") or {}).get("name", "Backlog") == "Backlog":
            sprint1_backlog.append(item)

print(f"Sprint 1 total: {len(sprint1_all)} items")
print(f"  Already Done/In Progress/etc.: {len(sprint1_all) - len(sprint1_backlog)}")
print(f"  To update to 'This Sprint': {len(sprint1_backlog)}")

ok = 0
for i, item in enumerate(sprint1_backlog):
    num = (item.get("content") or {}).get("number", "?")
    r = subprocess.run([
        "gh", "api", "graphql", "-f", f"""query=mutation {{
  updateProjectV2ItemFieldValue(input: {{
    projectId: "{PROJECT_ID}"
    itemId: "{item['id']}"
    fieldId: "{STATUS_FIELD_ID}"
    value: {{ singleSelectOptionId: "{THIS_SPRINT_OPTION_ID}" }}
  }}) {{ projectV2Item {{ id }} }}
}}"""
    ], capture_output=True, text=True)
    result = json.loads(r.stdout)
    if "errors" in result:
        print(f"  ✗ #{num}: {result['errors'][0]['message'][:60]}")
    else:
        ok += 1
    if (i + 1) % 10 == 0:
        print(f"  Updated {i+1}/{len(sprint1_backlog)}...")
    time.sleep(0.05)

print(f"\n✓ {ok}/{len(sprint1_backlog)} items set to 'This Sprint'")
print(f"  Board: https://github.com/orgs/{ORG}/projects/{PROJECT_NUM}/views/4")
