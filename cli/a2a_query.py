"""
rest_api.py

Version : 1.9.5
Author  : aumezawa
"""

import argparse
import time
from typing import Any
from uuid import uuid4

import httpx
import httpx_sse


def get_agnet_card(
    url: str,
    route: str = "/.well-known/agent-card.json",
) -> tuple[str, bool]:
    """Get Agent Card."""
    with httpx.Client(timeout=60) as client:
        response = client.get(f"{url}{route}")
        result = response.json()
        print("=== Get Agent Card ===")
        print(result)
        print()
        return (result.get("url", ""), result.get("capabilities", {}).get("streaming", False))


def make_message(
    query: str,
    context_id: str | None = None,
) -> dict[str, Any]:
    """Make Message."""
    return {
        "message": {
            "messageId": str(uuid4()),
            "contextId": context_id or str(uuid4()),
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
    with httpx.Client(timeout=60) as client:
        response = client.get(
            url=f"{url}{api_version}/tasks/{task_id}",
        )
        result = response.json()
        print(f"=== Get Task (task_id={task_id}) ===")
        print(result)
        print()
        if result.get("status", {}).get("state", "") in ["TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"]:
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
    with httpx.Client(timeout=60) as client:
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
        if result.get("task", {}).get("status", {}).get("state", "") in ["TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"]:
            for _ in range(retry_out):
                if not get_task(url=url, task_id=result.get("task", {}).get("id", "")):
                    break
                time.sleep(1)


def post_message_stream(
    url: str,
    query: str,
    context_id: str | None = None,
    api_version: str = "/v1",
) -> None:
    """Post Message with SSE."""
    with httpx_sse.connect_sse(
        client=httpx.Client(),
        method="POST",
        url=f"{url}{api_version}/message:stream",
        headers={
            "Content-Type": "application/json",
        },
        json=make_message(query, context_id),
    ) as event_source:
        for sse in event_source.iter_sse():
            print(sse.json())
            print()


def a2a_query() -> None:
    """Execute a selected function."""
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
        (url, streaming) = get_agnet_card(url)

        if not url:
            msg = "No url in the agent card."
            raise ValueError(msg)

        if streaming:
            post_message_stream(url=url, query=args.query, context_id=args.context_id)
        else:
            post_message(url=url, query=args.query, context_id=args.context_id)
        return

    print(parser.format_help())


if __name__ == "__main__":
    a2a_query()
