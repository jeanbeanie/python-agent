import os
import httpx
from datetime import datetime
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

@tool
async def github_profile(owner: str , name: str) -> str: 
    # TODO set github name in env instead
    # TODO pull list of recent repos if none is provided and let user choose
    """Pull recent commits/stars for a given repo name provided by the user. Use this when the user asks about their own Github projects, or about their latest Github stars and or commits."""
   
    print('going into github tool!')

    # build GraphQL query using user input
    query = """
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            stargazerCount
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 5) {
                            nodes { message committedDate }
                        }
                    }
                }
            }
        }
    }
    """

    url = "https://api.github.com/graphql"
    token = os.environ['GITHUB_TOKEN']
    if not token:
        return("Couldn't reach GitHub: GITHUB_TOKEN is not set in your .env or environment!")

    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
    }

    # GraphQL expects a JSON payload with "query"
    payload = { 
        "query": query,
        "variables": {"owner": owner, "name":name}
    }

    # send GraphQL query as POST request
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
   
    result = response.json()

    # errors array is returned for missing repos/ bad queries
    if "errors" in result:
        return f"Github API error: {result['error'][0]['message']}"

    # handle missing/mispelled repo
    repo = result["data"]["repository"]
    if repo is None:
        return f"No repo found for {owner}/{name}. Check spelling and try again!"

    repo_stars = repo["stargazerCount"]

    # defaultBranchRef is none for repos with no commits
    branch = repo.get("defaultBranchRef")
    if branch is None:
        return f"\n This repo currently has {repo_stars} stars. It doesn't have any commits yet... get to work!"

    # finally safe to grab the repo commits
    repo_commits = branch["target"]["history"]["nodes"]

    lines = []

    for commit in repo_commits:
        # Parse the returned ISO string (replace 'Z' with '+00:00' for standard parsing)
        date = datetime.fromisoformat(commit["committedDate"].replace("Z", "+00:00"))
        lines.append(f"{date:%A, %b %d %Y} - {commit['message']}")

    return f"\n This repo currently has {repo_stars} stars.\n Here are the latest commits pushed:\n {lines}"

