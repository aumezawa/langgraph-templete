"""
main.py

Version : 2.0.0
Author  : aumezawa
"""

from __future__ import annotations

import argparse
import asyncio
from typing import TYPE_CHECKING
from uuid import uuid4

from dotenv import load_dotenv

from app.agents.chatbot import Chatbot
from app.libs.logger import setup_logger
from app.tools.a2a_client import A2aServer
from app.tools.currency_rate import tools as currency_rate_tools
from app.tools.mcp_client import McpServer

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

###
# Set API Key
###
load_dotenv()

###
# Setup logger
###
setup_logger()


async def get_tools_from_a2a_server(url: str | None = None) -> list[BaseTool]:
    """Execute Chatbot."""
    a2a_server = A2aServer(
        name="currency_rate",
        base_url=url or "http://localhost:8000/a2a/chatbot",
    )

    return await a2a_server.get_tools()


async def exec_chatbot(
    query: str,
    *,
    streaming: bool = False,
    mcp_url: str | None = None,
    a2a_url: str | None = None,
    raw_output: bool = False,
) -> None:
    """Execute chatbot."""
    if mcp_url:
        mcp_server = McpServer(
            name="currency_rate",
            server_url=mcp_url,
            transport="streamable_http",
        )
        tools = await mcp_server.get_tools()
    elif a2a_url:
        tools = await get_tools_from_a2a_server(url=a2a_url)
    else:
        tools = currency_rate_tools

    chatbot = Chatbot(
        tools=tools,
        strict=False,
    )

    # Prepare
    thread_id = str(uuid4())
    print("=== Run ===")
    print(f"query: {query}, streaming: {streaming}, strict: {False}, thread id: {thread_id}")
    print()

    # Execute
    if not streaming:
        result, _ = await chatbot.async_run(
            query=query,
            thread_id=thread_id,
            raw_output=raw_output,
        )
        # Result
        print("=== Result ===")
        print(result)
        print()
        print("=== Checkpoint ===")
        print(chatbot.checkpoint(thread_id))
        print()

    else:
        async for event, _ in chatbot.astream_run(
            query=query,
            thread_id=thread_id,
            raw_output=raw_output,
        ):
            # Result
            print("=== Event ===")
            print(event)
            print()
        print("=== Checkpoint ===")
        print(chatbot.checkpoint(thread_id))
        print()


async def exec_chatbot_interactive(
    *,
    streaming: bool = False,
    strict: bool = False,
    mcp_url: str | None = None,
    a2a_url: str | None = None,
    raw_output: bool = False,
) -> None:
    """Execute conversations with Chatbot."""
    if mcp_url:
        mcp_server = McpServer(
            name="currency_rate",
            server_url=mcp_url,
            transport="streamable_http",
        )
        tools = await mcp_server.get_tools()
    elif a2a_url:
        tools = await get_tools_from_a2a_server(url=a2a_url)
    else:
        tools = currency_rate_tools

    chatbot = Chatbot(
        tools=tools,
        strict=strict,
    )

    # Prepare
    thread_id = str(uuid4())
    print("=== Run ===")
    print(f"streaming: {streaming}, strict: {strict}, thread id: {thread_id}")
    print()

    print("=== Chatting ===")
    print("Starting chatting with chatbot. Input no message to halt.")
    print()
    resume = False
    while True:
        query = input("Your input : ")

        if not query:
            break

        if not streaming:
            result, interrupt = await chatbot.async_run(
                query=query,
                thread_id=thread_id,
                resume=resume,
                raw_output=raw_output,
            )
            resume = interrupt
            print(f"AI output  : {result}")
            print()

        else:
            async for event, interrupt in chatbot.astream_run(
                query=query,
                thread_id=thread_id,
                resume=resume,
                raw_output=raw_output,
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
        choices=["chatbot"],
        help="Specify an agent to execute.",
    )
    parser.add_argument(
        "-q",
        "--query",
        default=None,
        help="Specify a query or question.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Enable interactive mode.",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Enable streaming mode.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode.",
    )
    parser.add_argument(
        "-mcp",
        "--remote-mcp",
        default=None,
        help="Specify the url to bind tools on the remote MCP server.",
    )
    parser.add_argument(
        "-a2a",
        "--remote-a2a",
        default=None,
        help="Specify the url to bind tools on the remote A2A server.",
    )
    parser.add_argument(
        "-o",
        "--raw-output",
        action="store_true",
        help="Enable raw output mode.",
    )
    args = parser.parse_args()

    if args.interactive:
        if args.agent == "chatbot":
            asyncio.run(
                exec_chatbot_interactive(
                    streaming=args.streaming,
                    strict=args.strict,
                    mcp_url=args.remote_mcp,
                    a2a_url=args.remote_a2a,
                    raw_output=args.raw_output,
                ),
            )
        return

    if args.query is not None:
        if args.agent == "chatbot":
            asyncio.run(
                exec_chatbot(
                    args.query,
                    streaming=args.streaming,
                    mcp_url=args.remote_mcp,
                    a2a_url=args.remote_a2a,
                    raw_output=args.raw_output,
                ),
            )
        return

    parser.print_help()


if __name__ == "__main__":
    query()
