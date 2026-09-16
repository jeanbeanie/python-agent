import asyncio
import httpx
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
#from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from python_agent.tools.github_profile import github_profile
from python_agent.tools.hacker_news import hacker_news_stories


load_dotenv()

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
