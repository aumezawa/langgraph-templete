"""
run_a2a_server.py

Version : 2.0.0
Author  : aumezawa
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from app.a2a_agents.a2a_chatbot import A2aChatbot
from app.libs.logger import setup_logger

###
# Set API Key
###
load_dotenv()

###
# Setup logger
###
setup_logger()


def exec_a2a_chatbot(*, streaming: bool = True, blocking: bool = True, strict: bool = False) -> None:
    """Execute A2A Chatbot."""
    a2a_chatbot = A2aChatbot(streaming=streaming, blocking=blocking, strict=strict)
    a2a_chatbot.run()


def run_a2a_server() -> None:
    """Execute a selected function."""
    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        required=True,
        choices=["chatbot"],
        help="Specify an a2a server to execute.",
    )
    parser.add_argument(
        "-nb",
        "--non-blocking",
        action="store_true",
        help="Enable non-blocking mode.",
    )
    parser.add_argument(
        "-st",
        "--streaming",
        action="store_true",
        help="Enable streaming mode.",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="Enable strict mode.",
    )
    args = parser.parse_args()

    if args.agent == "chatbot":
        exec_a2a_chatbot(streaming=args.streaming, blocking=not args.non_blocking, strict=args.strict)
        return

    parser.print_help()


if __name__ == "__main__":
    run_a2a_server()
