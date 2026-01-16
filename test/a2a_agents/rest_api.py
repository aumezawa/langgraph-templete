"""
rest_api.py

Version : 1.5.0
Author  : aumezawa
"""

import httpx
from typing import Any
from uuid import uuid4

def get_agnet_card(
    url: str,
    route: str = "/.well-known/agent-card.json",
) -> None:
    """Get Agent Card."""
    with httpx.Client(timeout=60.0) as client:
        response = client.get(f"{url}{route}")
        print("=== Get Agent Card ===")
        print(response.json())
        print()


def make_message(
    query: str,
    context_id: str | None = None,
) -> dict[str, Any]:
    """Make Message"""
    return {
        "message": {
            "messageId": uuid4().hex,
            "contextId": context_id or uuid4().hex,
            "role": "ROLE_USER",
            "content": [
                {
                    "text": f"{query}",
                },
            ],
        },
    }


def post_message(
    url: str,
    query: str,
    context_id: str | None = None,
    api_version: str = "/v1",
) -> None:
    """Post Message."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            url=f"{url}{api_version}/message:send",
            headers={
                "Content-Type": "application/json",
            },
            json=make_message(query, context_id),
        )
        print(f"=== Send Message (query={query}, context_id={context_id}) ===")
        print(response.json())
        print()


if __name__ == "__main__":
    """Execute a selected function."""
    import argparse

    parser = argparse.ArgumentParser(description="Select to execute an agent.")
    parser.add_argument(
        "-a",
        "--agent",
        choices=["a2a_chatbot"],
        help="The agent to execute.",
    )
    parser.add_argument(
        "-q",
        "--query",
        required=True,
        help="The query to the agent.",
    )
    parser.add_argument(
        "-c",
        "--context-id",
        default=None,
        help="The context ID for the conversation.",
    )
    args = parser.parse_args()

    if args.agent == "a2a_chatbot":
        url = "http://localhost:8000/a2a/chatbot"
        get_agnet_card(url)
        post_message(url, query=args.query, context_id=args.context_id)
    else:
        print(parser.format_help())
