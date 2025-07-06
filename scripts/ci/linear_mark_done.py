# scripts/linear_mark_done.py

"""
Mark a Linear issue as “Done” after the PR that references it is merged.

Usage (from GitHub Actions):
    python scripts/linear_mark_done.py "$BRANCH_NAME"
"""

from __future__ import annotations

import os
import re
import sys

import requests

ISSUE_RE = re.compile(r"\b([A-Za-z]{2,8}-\d+)\b", re.I) # e.g. CRA-27
branch = sys.argv[1]

m = ISSUE_RE.search(branch)
if not m:
    print("::warning:: no Linear issue key found in branch name")
    sys.exit(0)

issue_key = m.group(1)
api_key = os.environ["LINEAR_API_KEY"]

# 1️⃣ look up the issue + its current workflow state IDs
qry = """
query($key:String!){
  issue(key:$key){ id state{ id } team{ key } }
}
"""
resp = requests.post(
    "https://api.linear.app/graphql",
    json={"query": qry, "variables": {"key": issue_key}},
    headers={"Authorization": api_key},
    timeout=20,
).json()

issue_id = resp["data"]["issue"]["id"]
team_key = resp["data"]["issue"]["team"]["key"]

# 2️⃣ lookup the team’s “Done” state once
state_qry = """
query($team:String!){
  workflowStates(filter:{team:{key:{eq:$team}}}){ nodes{id name type} }
}
"""
states = requests.post(
    "https://api.linear.app/graphql",
    json={"query": state_qry, "variables": {"team": team_key}},
    headers={"Authorization": api_key},
    timeout=20,
).json()["data"]["workflowStates"]["nodes"]

done_id = next(s["id"] for s in states if s["type"] == "completed")

# 3️⃣ patch the issue
mut = """
mutation($id:String!,$st:String!){
  issueUpdate(id:$id,input:{stateId:$st}){ success }
}
"""
requests.post(
    "https://api.linear.app/graphql",
    json={"query": mut, "variables": {"id": issue_id, "st": done_id}},
    headers={"Authorization": api_key},
    timeout=20,
).raise_for_status()

print(f"✅ {issue_key} moved to Done")
