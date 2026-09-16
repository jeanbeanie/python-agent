import asyncio
import httpx
import os

from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


load_dotenv()

@tool
async def github_profile(owner: str , name: str) -> str: 
    # TODO set github name in env instead
    # TODO pull list of recent repos if none is provided and let user choose
    """Pull recent commits/stars for a given repo name provided by the user. Use this when the user asks about their own coding progress, or about their latest Github stars and or commits."""
   
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
    if "errors" in result;
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

    return f"\n This repo currently has {repoStars} stars.\n Here are the latest commits pushed:\n {lines}"

@tool
async def hacker_news_stories(limit: int=5) -> str:
    """Fetch the current top stories from Hacker News. Use this when the user asks about tech news, or what's trending on Hacker News."""
    print('going into hacker news tool!')
    url = "https://hn.algolia.com/api/v1/search"

    # httpx URL encodes this into ?tags=front_page&hitsPerPage=N
    params = {"tags": "front_page", "hitsPerPage": limit}

    # close connection pool when done, exceptions fail after 10 seconds
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        # raise HTTPStatusError on 4xx/5xx instead of parsing the JSON
        response.raise_for_status()

    stories = response.json()["hits"]
    lines = []

    for i, story in enumerate(stories, start=1):
        title = story["title"]
        points = story["points"]
        # build clickable link from story's objectID
        link = f"https://news.ycombinator.com/item?id={story['objectID']}"
        lines.append(f"{i}. {title} ({points} points) - {link}")
    # fed back to the LLM as the "tool result" for the model to use in its overall response
    return "\n".join(lines)


async def main():
    model = ChatOpenAI(temperature=0)

    tools= [hacker_news_stories, github_profile]
    agent_executor = create_react_agent(model, tools)

    print("Heya! Type quit to exit this chat.")

    messages_history = []

    while True:
        # ask user for some input
        # NOTE: not async for now
        user_input = input("\nYou: ").strip()

        if user_input == "quit":
            break
        print("\nAssistant: ", end="")

        # add new message to persistent history
        messages_history.append(HumanMessage(content=user_input))

        # stream updates
        async for chunk in agent_executor.astream(
            {"messages": messages_history}
        ): # take response from agent stream, print to console
            if "agent" in chunk and "messages" in chunk["agent"]:
                for message in chunk["agent"]["messages"]:
                    # Print content if the message has a content property
                    if hasattr(message, "content") and message.content:
                        print(message.content, end="", flush=True)
        print()

if __name__ == "__main__":
    # asyncio.run() first creates the event loop, runs main() to completion,
    # then closes it, allows calling async funcs
    asyncio.run(main())
