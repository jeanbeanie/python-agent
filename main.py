from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv()

def main():
    model = ChatOpenAI(temperature=0)

    tools= []
    agent_executor = create_react_agent(model, tools)

    print("Heya! Type quit to exit this chat.")

    while True:
        # ask user for some input
        user_input = input("\nYou: ").strip()

        if user_input == "quit":
            break
        print("\nAssistant: ", end="")
        # send user input to agent
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]}
        ): # take response from agent stream, print to console
            if "agent" in chunk and "messages" in chunk["agent"]:
                for message in chunk["agent"]["messages"]:
                    # Print content if the message has a content property
                    if hasattr(message, "content") and message.content:
                        print(message.content, end="", flush=True)
        print()

if __name__ == "__main__":
    main()
