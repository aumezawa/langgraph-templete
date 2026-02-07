"""
main.py

Version : 1.9.5
Author  : aumezawa
"""

import argparse

from dotenv import load_dotenv

from app.a2a_agents.a2a_chatbot import A2aChatbot

###
# Set API Key
###
load_dotenv()


def exec_a2a_chatbot(*, streaming: bool = True, blocking: bool = True) -> None:
    """Execute A2A Chatbot."""
    a2a_chatbot = A2aChatbot(streaming=streaming, blocking=blocking)
    a2a_chatbot.run()


def run_server() -> None:
    """Execute a selected function."""
    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        default="a2a_chatbot",
        choices=["a2a_chatbot"],
        help="Specify an agent server to execute.",
    )
    parser.add_argument(
        "-m",
        "--a2a-mode",
        default="blocking",
        choices=["blocking", "non-blocking", "streaming"],
        help="A2A mode.",
    )
    args = parser.parse_args()

    if args.agent == "a2a_chatbot":
        if args.a2a_mode == "blocking":
            exec_a2a_chatbot(streaming=False, blocking=True)
        elif args.a2a_mode == "non-blocking":
            exec_a2a_chatbot(streaming=False, blocking=False)
        elif args.a2a_mode == "streaming":
            exec_a2a_chatbot(streaming=True)

    print(parser.format_help())


if __name__ == "__main__":
    run_server()
