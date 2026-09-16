import httpx
from langchain.tools import tool

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

