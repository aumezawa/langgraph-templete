"""
main.py

Version : 1.4.0
Author  : aumezawa
"""

import os
import sys
from dotenv import load_dotenv
from uuid import uuid4

sys.path.append(os.path.curdir)


###
# Set API Key
###
load_dotenv()


def exec_chatbot() -> None:
    """Execute chatbot."""
    from app.agents.chatbot import Chatbot
    from app.tools.math import tools as math_tools

    chatbot = Chatbot(
        tools=math_tools,
    )

    # Execute
    thread_id = uuid4().hex
    result = chatbot.run(
        query="100掛ける200の計算と1足す2の計算をそれぞれしてください",
        thread_id=thread_id,
    )

    print("=== Result ===")
    print(result)
    print("=== Checkpoint ===")
    print(chatbot.checkpoint(thread_id))


def exec_passive_goal_creater() -> None:
    """Execute Passive Goal Creater."""
    from app.agents.passive_goal_creater import PassiveGoalCreater

    goal_creater = PassiveGoalCreater()

    # Execute
    result = goal_creater.run(
        query="カレーの作り方",
    )

    print("=== Result ===")
    print(result)


def main() -> None:
    """Execute a selected function."""
    import argparse

    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        choices=["chatbot", "passive_goal_creater"],
        help="The agent to execute.",
    )
    args = parser.parse_args()

    if args.agent == "chatbot":
        exec_chatbot()
    elif args.agent == "passive_goal_creater":
        exec_passive_goal_creater()
    else:
        print(parser.format_help())


if __name__ == "__main__":
    main()
