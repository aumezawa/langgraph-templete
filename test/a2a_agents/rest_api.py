"""
rest_api.py

Version : 1.5.0
Author  : aumezawa
"""

import httpx
from typing import Any


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
) -> dict[str, Any]:
    """Make Message"""
    return {
        "message": {
            "messageId": "sample",
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
    api_version: str = "/v1",
) -> None:
    """Post Message."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            url=f"{url}{api_version}/message:send",
            headers={
                "Content-Type": "application/json",
            },
            json=make_message(query),
        )
        print(f"=== Send Message (query={query}) ===")
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
    args = parser.parse_args()

    if args.agent == "a2a_chatbot":
        url = "http://localhost:8000/a2a/chatbot"
        query = "100掛ける200を計算して"
        get_agnet_card(url)
        post_message(url, query=query)
    else:
        print(parser.format_help())
