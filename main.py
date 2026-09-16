import asyncio
import httpx
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from python_agent.tools.github_profile import github_profile

load_dotenv()


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
