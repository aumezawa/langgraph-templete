"""
mcp.py

Version : 1.7.0
Author  : aumezawa
"""

import httpx
from typing import Any
from pydantic import BaseModel, Field
from uuid import uuid4
from a2a.client import ClientConfig, ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.types import AgentCard, Message, Part, Role, TransportProtocol, TextPart
from langchain_core.tools import BaseTool, StructuredTool


class RequestMessage(BaseModel):
    """Request Message Schema."""

    text: str = Field(
        ...,
        description="A message or messages you ask to another agent.",
    )
    message_id: str | None = Field(
        default=None,
        description="A unique identifier for the message, typically a UUID. "
        "The corresponding response from the agent contains the same message_id.",
    )
    context_id: str | None = Field(
        default=None,
        description="A unique identifier that logically groups multiple related the messages, "
        "typically a UUID. If you want to continue the conversation, set the same ID "
        "which was set in the previouse messages. When you starts a new conversation, the ID "
        "is not required, and the agent will send a new context id in the response message.",
    )


class A2aServer:
    """MCP Server Class."""

    def __init__(
        self,
        name: str,
        base_url: str,
        agent_card_path: str = "/.well-known/agent-card.json",
        transports: list[TransportProtocol | str] | None = None,
        api_token: str | None = None,
    ) -> None:
        """Initialize A2A Server."""
        self.name = name
        self.base_url = base_url
        self.agent_card_path = agent_card_path
        self.transports = transports or ["JSON-RPC", "HTTP+JSON"]
        self.api_token = api_token

    async def get_agent_card(self) -> AgentCard:
        """Get agent card from A2A server."""
        resolver = A2ACardResolver(
            base_url=self.base_url,
            httpx_client=httpx.AsyncClient(),
            agent_card_path=self.agent_card_path,
        )
        return await resolver.get_agent_card()

    async def get_tools(self) -> list[BaseTool]:
        """Get tools on A2A server."""
        agent_card = await self.get_agent_card()

        factory = ClientFactory(
            config=ClientConfig(
                streaming=False,
                polling=False,
                httpx_client=None,
                supported_transports=self.transports,
                accepted_output_modes=[
                    "text",
                    "text/plain",
                ],
                push_notification_configs=[
                ],
                extensions=[
                ],
            ),
        )

        client = factory.create(card=agent_card)

        async def send_message(
            text: str,
            message_id: str | None = None,
            context_id: str | None = None,
        ) -> dict[str, Any]:
            message = Message(
                message_id=message_id or uuid4().hex,
                context_id=context_id or uuid4().hex,
                role=Role.user,
                parts=[
                    Part(root=TextPart(text=text)),
                ],
            )
            result = ""
            async for response in client.send_message(message):
                if isinstance(response, Message):
                    for part in response.parts:
                        if part.root.kind == "text" and isinstance(part.root.text, str):
                            result = result + part.root.text
                    context_id = response.context_id or context_id
                elif isinstance(response, tuple):
                    ### wip: (task, event) _ response
                    pass
                else:
                    return {
                        "message_id": message_id,
                        "context_id": context_id,
                        "content":[],
                        "isError": True,
                    }
            return {
                "message_id": message_id,
                "context_id": context_id,
                "content": [
                    {
                        "type": "text",
                        "text": result,
                    },
                ],
                "isError": False,
            }

        return [
            StructuredTool.from_function(
                name=agent_card.name,
                description=agent_card.description,
                args_schema=RequestMessage,
                coroutine=send_message,
                response_format="content",
            ),
        ]
