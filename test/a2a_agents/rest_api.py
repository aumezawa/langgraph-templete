"""
rest_api.py

Version : 1.8.0
Author  : aumezawa
"""

import httpx
import time
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


def get_task(
    url: str,
    task_id: str,
    api_version: str = "/v1",
) -> bool:
    """Get Task."""
    with httpx.Client(timeout=60.0) as client:
        response = client.get(
            url=f"{url}{api_version}/tasks/{task_id}",
        )
        result = response.json()
        print(f"=== Get Task (task_id={task_id}) ===")
        print(result)
        print()
        if result.get("status") and result["status"]["state"] in ["TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"]:
            return True
    return False


def post_message(
    url: str,
    query: str,
    context_id: str | None = None,
    api_version: str = "/v1",
    retry_out: int = 60,
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
        result = response.json()
        print(f"=== Send Message (query={query}, context_id={context_id}) ===")
        print(result)
        print()
        if result.get("task"):
            for _ in range(retry_out):
                if not get_task(url=url, task_id=result["task"]["id"]):
                    break
                time.sleep(1)


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
