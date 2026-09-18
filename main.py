import asyncio
import httpx
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
#from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from python_agent.tools.github_profile import github_profile
from python_agent.tools.hacker_news import hacker_news_stories


load_dotenv()

EXIT_WORDS = ("quit", "exit", "q", "goodbye", "bye")

async def main():
    model = ChatOpenAI(temperature=0)

    tools= [hacker_news_stories, github_profile]
    agent_executor = create_react_agent(model, tools, checkpointer=MemorySaver())
    
    # thread_id names ONE conversation/chat
    # every call that passes this config reads/writes the same saved state
    config = {"configurable": {"thread_id": "my-chat"}}

    print("Heya! Type quit to exit this chat.")

    while True:
        # ask user for some input
        user_input = (await asyncio.to_thread(input, "\nYou: ")).strip()

        if user_input.lower() in EXIT_WORDS:
            break
        # if user hits enter with nothing typed, ask again
        if not user_input:
            continue

        print("\nAssistant: ", end="")


        # before running, the graph loads the saved state for "my-chat",
        # appends the new message to it, then starts the ReAct loop
        async for token, metadata in agent_executor.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
        ): 
            # "in messages" mode chunk has token and metadata
            # token (AIMessageChunk containing a fragment, models can send empty .content while thinking)
            # metadata (dict describing if frag came from agent or tool)
            if metadata.get("langgraph_node") == "agent" and token.content:
                # end="" no new line after each frag, 
                # flush pushes each frag to the terminal immediately versus in one burst at the end
                print(token.content, end="", flush=True)
        print()

if __name__ == "__main__":
    # asyncio.run() first creates the event loop, runs main() to completion,
    # then closes it, allows calling async funcs
    asyncio.run(main())

