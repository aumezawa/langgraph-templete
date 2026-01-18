"""
main.py

Version : 1.9.0
Author  : aumezawa
"""

import argparse
import asyncio
from uuid import uuid4

from dotenv import load_dotenv

from app.a2a_agents.a2a_chatbot import A2aChatbot
from app.agents.chatbot import Chatbot
from app.agents.passive_goal_creater import PassiveGoalCreater
from app.tools.a2a_client import A2aServer
from app.tools.math import tools as math_tools

###
# Set API Key
###
load_dotenv()


async def exec_chatbot() -> None:
    """Execute chatbot."""
    chatbot = Chatbot(
        tools=math_tools,
    )

    # Execute
    thread_id = uuid4().hex
    result = await chatbot.async_run(
        query="100掛ける200の計算と1足す2の計算をそれぞれしてください",
        thread_id=thread_id,
    )

    print("=== Result ===")
    print(result)
    print()
    print("=== Checkpoint ===")
    print(chatbot.checkpoint(thread_id))


def exec_passive_goal_creater() -> None:
    """Execute Passive Goal Creater."""
    goal_creater = PassiveGoalCreater()

    # Execute
    result = goal_creater.run(
        query="カレーの作り方",
    )

    print("=== Result ===")
    print(result)


def exec_a2a_chatbot(*, streaming: bool = True, blocking: bool = True) -> None:
    """Execute A2A Chatbot."""
    a2a_chatbot = A2aChatbot(streaming=streaming, blocking=blocking)
    a2a_chatbot.run()


async def exec_orchestrator() -> None:
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

    # Execute
    thread_id = uuid4().hex
    async for event in await chatbot.astream_run(
        query="100掛ける200の計算と1足す2の計算をそれぞれしてください",
        thread_id=thread_id,
    ):
        print("=== Event ===")
        print(event)
        print()


def main() -> None:
    """Execute a selected function."""
    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        choices=["chatbot", "passive_goal_creater", "a2a_chatbot", "orchestrator"],
        help="The agent to execute.",
    )
    parser.add_argument(
        "-m",
        "--a2a-mode",
        choices=["direct", "basic", "streaming"],
        help="A2A mode.",
    )
    args = parser.parse_args()

    if args.agent == "chatbot":
        asyncio.run(exec_chatbot())
    elif args.agent == "passive_goal_creater":
        exec_passive_goal_creater()
    elif args.agent == "a2a_chatbot":
        if args.a2a_mode == "direct":
            exec_a2a_chatbot(streaming=False, blocking=True)
        elif args.a2a_mode == "basic":
            exec_a2a_chatbot(streaming=False, blocking=False)
        elif args.a2a_mode == "streaming":
            exec_a2a_chatbot(streaming=True)
    elif args.agent == "orchestrator":
        asyncio.run(exec_orchestrator())
    else:
        print(parser.format_help())


if __name__ == "__main__":
    main()
