# scripts/ci/linear_mark_done.py
"""
Move a Linear issue to the team's “Completed” state after the PR that
references it has been merged.

Usage (from GitHub Actions):
    python scripts/ci/linear_mark_done.py "$BRANCH_NAME"
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

import requests

BRANCH = sys.argv[1]

# Match both CRA-186 and cra-186-something-else
m = re.search(r"\b([A-Za-z]{2,8})-(\d+)\b", BRANCH, re.I)
if not m:
    print("::warning:: no Linear key found in branch name")
    sys.exit(0)

TEAM_PREFIX, NUM = m.group(1).upper(), int(m.group(2))

API_KEY = os.getenv("LINEAR_API_KEY")
if not API_KEY:
    print("::error:: env LINEAR_API_KEY not set")
    sys.exit(1)

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}


def gql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Tiny wrapper that exits with ::error:: if Linear returns GraphQL errors."""
    res = requests.post(
        "https://api.linear.app/graphql",
        json={"query": query, "variables": variables},
        headers=HEADERS,
        timeout=20,
    ).json()

    if "errors" in res:
        print(f"::error:: Linear errors: {res['errors']}")
        sys.exit(1)
    return res["data"]  # type: ignore[no-any-return]


# 1️⃣  Find the issue by team-key + number
data = gql(
    """
    query($team:String!,$nr:Float!){
      issues(
        filter:{
          team:{key:{eq:$team}}
          number:{eq:$nr}
        }
      ){
        nodes{
          id
          state{ id type }
          team{ id key }
        }
      }
    }
    """,
    {"team": TEAM_PREFIX, "nr": float(NUM)},  # Float to satisfy schema
)

nodes = data["issues"]["nodes"]
if not nodes:
    print(f"::warning:: issue {TEAM_PREFIX}-{NUM} not found in Linear")
    sys.exit(0)

issue_id = nodes[0]["id"]
team_key = nodes[0]["team"]["key"]

# 2️⃣  Fetch that team’s “completed” workflow-state
states = gql(
    """
    query($team:String!){
      workflowStates(
        filter:{ team:{key:{eq:$team}} }
      ){ nodes{ id type } }
    }
    """,
    {"team": team_key},
)["workflowStates"]["nodes"]

done_state = next((s["id"] for s in states if s["type"] == "completed"), None)
if not done_state:
    print(f"::error:: completed state not found for team {team_key}")
    sys.exit(1)

# 3️⃣  Update the issue
gql(
    """
    mutation($id:String!,$st:String!){
      issueUpdate(id:$id,input:{stateId:$st}){ success }
    }
    """,
    {"id": issue_id, "st": done_state},
)

print(f"✅ {TEAM_PREFIX}-{NUM} marked Done")
