# python-agent

A terminal chat agent (LangChain/LangGraph + OpenAI) with tools for active coders.

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

Create a `.env` file with:

```
OPENAI_API_KEY=...
GITHUB_TOKEN=...
```

## Usage

```bash
uv run main.py
```

Chat to your heart's content; type `quit` to exit.

## Tools

- `hacker_news_stories` : fetches current Hacker News front-page stories
- `github_profile` : fetches a GitHub repo's star count and recent commits

## Future TODO

- pull in relevant techy subreddits top posts
- resume quality check tool, compare resume file to passed in job posting link
- maybe add ability to check email for unread tech newsletter/jobs related stuff
