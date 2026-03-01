"""
a2a_client.py

Version : 2.0.0
Author  : aumezawa
"""

from __future__ import annotations

import functools
import operator
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.client.card_resolver import A2ACardResolver
from a2a.types import AgentCard, Message, Part, Role, TaskQueryParams, TaskState, TextPart, TransportProtocol
from langchain_core.messages.content import TextContentBlock, create_text_block
from langchain_core.tools import BaseTool, StructuredTool, ToolException
from loguru import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig

TASK_RETRY_OUT = 60


class RequestMessage(BaseModel):
    """Request Message Schema."""

    text: str = Field(
        ...,
        description="A message or messages you ask to another agent.",
    )
    """
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
    """


class A2aServer:
    """MCP Server Class."""

    def __init__(
        self,
        name: str,
        base_url: str,
        *,
        agent_card_path: str = "/.well-known/agent-card.json",
        transports: list[TransportProtocol | str] | None = None,
        streaming: bool = False,
        api_token: str | None = None,
    ) -> None:
        """Initialize A2A Server."""
        self.name = name
        self.base_url = base_url
        self.agent_card_path = agent_card_path
        self.transports = transports or ["JSON-RPC", "HTTP+JSON"]
        self.streaming = streaming
        self.api_token = api_token
        self.http_headers = (
            {
                "Authorization": f"Bearer {api_token}",
            }
            if api_token
            else None
        )
        self.task_id_store: dict[str, str] = {}

    async def get_agent_card(self) -> AgentCard:
        """Get agent card from A2A server."""
        resolver = A2ACardResolver(
            base_url=self.base_url,
            httpx_client=httpx.AsyncClient(
                headers=self.http_headers,
            ),
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
                httpx_client=httpx.AsyncClient(
                    headers=self.http_headers,
                ),
                supported_transports=self.transports,
                accepted_output_modes=[
                    "text",
                    "text/plain",
                ],
                push_notification_configs=[],
                extensions=[],
            ),
        )

        client = factory.create(card=agent_card)

        """
        def create_metadata(
            *,
            task_id: str | None = None,
            message_id: str | None = None,
            context_id: str | None = None,
        ) -> dict[str, Any]:
            return {
                "a2a_task_id": task_id,
                "a2a_message_id": message_id,
                "a2a_context_id": context_id,
            }
        """

        def extract_text(content: Message) -> str:
            return "".join(
                [
                    part.root.text if part.root.kind == "text" and isinstance(part.root.text, str) else ""
                    for part in content.parts
                ],
            )

        def convert_content(part: Part, meta: dict[str, Any] | None = None) -> TextContentBlock:
            if part.root.kind == "text" and isinstance(part.root.text, str):
                return create_text_block(text=part.root.text, extras=meta)
            msg = "Not supported content type"
            raise ToolException(msg)

        async def send_message(
            text: str,
            config: RunnableConfig,
        ) -> list[TextContentBlock]:
            thread_id = config.get("configurable", {}).get("thread_id") or str(uuid4())
            task_id = self.task_id_store.get(thread_id)
            message = Message(
                message_id=str(uuid4()),
                task_id=task_id,
                context_id=thread_id,
                role=Role.user,
                parts=[
                    Part(root=TextPart(text=text)),
                ],
            )
            logger.debug(f"a2a send message: {message}")
            tool_contents: list[TextContentBlock] = []
            # Get result of message:send
            async for response in client.send_message(message):
                logger.debug(f"a2a response: {response}")
                if isinstance(response, Message):
                    tool_contents += [convert_content(part) for part in response.parts]
                else:
                    (task, _) = response
                    # Get result of task
                    retry = 0
                    while task.status.state in [TaskState.submitted, TaskState.working] and retry < TASK_RETRY_OUT:
                        task = await client.get_task(TaskQueryParams(id=task.id))
                        logger.debug(f"a2a response task: {task}")
                        retry += 1

                    if task.status.state == TaskState.completed:
                        if task.artifacts is not None:
                            tool_contents += functools.reduce(  # converting list of list to list
                                operator.iadd,
                                [[convert_content(part) for part in artifact.parts] for artifact in task.artifacts],
                                [],
                            )
                        if self.task_id_store.get(thread_id):
                            del self.task_id_store[thread_id]
                    elif task.status.state == TaskState.input_required:
                        if task.status.message is not None:
                            tool_contents += [convert_content(part) for part in task.status.message.parts]
                        self.task_id_store[thread_id] = task.id
                    else:
                        msg = extract_text(task.status.message) if task.status.message else "An unknown error occurred."
                        msg += f" task: {task_id}, status: {task.status.state}"
                        raise ToolException(msg)
            # Finally result
            return tool_contents

        return [
            StructuredTool(
                name=agent_card.name,
                description=agent_card.description,
                args_schema=RequestMessage,
                coroutine=send_message,
                response_format="content",
            ),
        ]
