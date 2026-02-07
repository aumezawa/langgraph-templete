"""
main.py

Version : 1.9.5
Author  : aumezawa
"""

import argparse
import asyncio
from uuid import uuid4

from dotenv import load_dotenv

from app.agents.chatbot import Chatbot
from app.tools.a2a_client import A2aServer
from app.tools.math import tools as math_tools

###
# Set API Key
###
load_dotenv()


async def exec_chatbot(query: str, mode: str = "single") -> None:
    """Execute chatbot."""
    chatbot = Chatbot(
        tools=math_tools,
    )

    # Prepare
    thread_id = str(uuid4())
    print("=== Run ===")
    print(f"query: {query}")
    print(f"mode: {mode}")
    print(f"thread id: {thread_id}")
    print()

    # Execute
    if mode == "single":
        result = await chatbot.async_run(
            query=query,
            thread_id=thread_id,
            raw_output=True,
        )

        # Result
        print("=== Result ===")
        print(result)
        print()
        print("=== Checkpoint ===")
        print(chatbot.checkpoint(thread_id))
        print()

    elif mode == "single_stream":
        async for event, _ in chatbot.astream_run(
            query=query,
            thread_id=thread_id,
        ):
            # Result
            print("=== Event ===")
            print(event)
            print()


async def exec_orchestrator(query: str, mode: str) -> None:
    """Execute Chatbot."""
    a2a_server = A2aServer(
        name="calcurator",
        base_url="http://localhost:8000/a2a/chatbot",
    )

    tools = await a2a_server.get_tools()

    chatbot = Chatbot(
        tools=tools,
        system_prompt="You are an orchestrator agent. Answer user's questions with tools you can use or other agents.",
    )

    # Prepare
    thread_id = str(uuid4())
    print("=== Run ===")
    print(f"query: {query}")
    print(f"mode: {mode}")
    print(f"thread id: {thread_id}")
    print()

    # Execute
    if mode == "single":
        result = await chatbot.async_run(
            query=query,
            thread_id=thread_id,
        )

        # Result
        print("=== Result ===")
        print(result)
        print()
        print("=== Checkpoint ===")
        print(chatbot.checkpoint(thread_id))
        print()

    elif mode == "single-stream":
        async for event in chatbot.astream_run(
            query=query,
            thread_id=thread_id,
        ):
            # Result
            print("=== Event ===")
            print(event)
            print()


async def chatting_chatbot() -> None:
    """Execute conversations with Chatbot."""
    chatbot = Chatbot(
        tools=math_tools,
    )
    thread_id = str(uuid4())

    print("=== Chatting ===")
    print("Starting chatting with chatbot. Input no message to halt.")
    print()
    resume = False
    while True:
        query = input("Your input : ")

        if not query:
            break

        async for event, interrupt in chatbot.astream_run(
            query=query,
            thread_id=thread_id,
            resume=resume,
        ):
            resume = interrupt
            print(f"AI output  : {event}")
            print()


def query() -> None:
    """Execute a selected function."""
    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        required=True,
        choices=["chatbot", "orchestrator"],
        help="Specify an agent to execute.",
    )
    parser.add_argument(
        "-q",
        "--query",
        default=None,
        help="A query or question.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default="single",
        choices=["single", "single-stream", "multi", "multi-stream"],
        help="Query mode",
    )
    args = parser.parse_args()

    if args.mode in ["multi", "multi-stream"]:
        if args.agent == "chatbot":
            asyncio.run(chatting_chatbot())
        elif args.agent == "orchestrator":
            pass
        return

    if args.query is not None:
        if args.agent == "chatbot":
            asyncio.run(exec_chatbot(args.query, args.mode))
        elif args.agent == "orchestrator":
            asyncio.run(exec_orchestrator(args.query, args.mode))
        return

    print(parser.format_help())


if __name__ == "__main__":
    query()
