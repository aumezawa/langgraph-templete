"""
a2a_chatbot.py

Version : 2.0.0
Author  : aumezawa
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, override

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AFastAPIApplication, A2ARESTFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_task, new_text_artifact
from loguru import logger

from app.agents.chatbot import Chatbot
from app.tools.currency_rate import tools as currency_rate_tools

if TYPE_CHECKING:
    from a2a.server.events import EventQueue

HTTP_PROTOCOL: Literal["http", "https"] = "http"
HTTP_HOST: str = "localhost"
HTTP_PORT: int = 8000
HTTP_ROUTE: str = "/a2a/chatbot"


class A2aChatbotExecutor(AgentExecutor):
    """A2A Chatbot Executor Class."""

    def __init__(
        self,
        *,
        streaming: bool = False,
        blocking: bool = True,
        strict: bool = False,
    ) -> None:
        """Initialize Chatbot Executor."""
        self.agent = Chatbot(
            tools=currency_rate_tools,
            strict=strict,
        )
        self.streaming = streaming
        self.blocking = blocking

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute Agent."""
        quary = context.get_user_input()

        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore[arg-type]
        task_state = task.status.state

        logger.debug(f"req, task: {task.id}, state: {task_state}, context: {task.context_id}, query: {quary}")

        try:
            # Streaming
            if self.streaming:
                if not self.blocking:
                    task.status.state = TaskState.working
                    task.artifacts = []
                    await event_queue.enqueue_event(task)
                    logger.debug(f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}")

                next_state = TaskState.completed
                async for event, interrupt in self.agent.astream_run(
                    query=quary,
                    thread_id=task.context_id,
                    resume=(task_state == TaskState.input_required),
                    raw_output=False,
                ):
                    if interrupt:
                        next_state = TaskState.input_required
                        break

                    await event_queue.enqueue_event(
                        TaskArtifactUpdateEvent(
                            artifact=new_text_artifact(
                                name="answer",
                                text=str(event),
                            ),
                            context_id=task.context_id,
                            task_id=task.id,
                        ),
                    )
                    logger.debug(
                        f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}, "
                        f"artifacts: {task.artifacts}",
                    )

                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=next_state),
                        context_id=task.context_id,
                        task_id=task.id,
                        final=True,
                    ),
                )
                logger.debug(f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}")

            # Non-streaming
            else:
                if not self.blocking:
                    task.status.state = TaskState.working
                    task.artifacts = []
                    await event_queue.enqueue_event(task)
                    logger.debug(f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}")

                result, interrupt = await self.agent.async_run(
                    query=quary,
                    thread_id=task.context_id,
                    resume=(task_state == TaskState.input_required),
                    raw_output=False,
                )

                if interrupt:
                    task.status.state = TaskState.input_required
                    task.status.message = new_agent_text_message(
                        text=str(result),
                        context_id=task.context_id,
                        task_id=task.id,
                    )
                    task.artifacts = []
                    await event_queue.enqueue_event(task)
                    logger.debug(
                        f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}, "
                        f"message: {task.status.message}",
                    )
                else:
                    task.status.state = TaskState.completed
                    task.artifacts = [new_text_artifact(name="answer", text=str(result))]
                    await event_queue.enqueue_event(task)
                    logger.debug(
                        f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}, "
                        f"artifacts: {task.artifacts}",
                    )

        except Exception as e:
            task.status.state = TaskState.failed
            task.status.message = new_agent_text_message(
                text=f"Error occurred during agent execution: {e}",
                context_id=task.context_id,
                task_id=task.id,
            )
            task.artifacts = []
            await event_queue.enqueue_event(task)
            logger.debug(
                f"res, task: {task.id}, state: {task.status.state}, context: {task.context_id}, "
                f"artifacts: {task.artifacts}",
            )

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel Agent Execution."""
        return


class A2aChatbot:
    """A2A Chatbot Class."""

    def __init__(
        self,
        *,
        mode: Literal["JSONRPC", "GRPC", "HTTP+JSON"] = "HTTP+JSON",
        streaming: bool = False,
        blocking: bool = True,
        strict: bool = False,
    ) -> None:
        """Initialize A2A Chatbot."""
        self.mode = mode
        self.agent_skill = AgentSkill(
            id="exchange_currency_rate",
            name="exchange_currency_rate",
            description="A chatbot that can exchange currency rates.",
            tags=["currency_rate"],
            input_modes=["text", "text/plain"],
            output_modes=["text", "text/plain"],
            examples=["How much is 1 USD in JPY?"],
        )
        self.agent_card = AgentCard(
            name="exchange_currency_rate_chatbot",
            description="A chatbot that can answer questions and exchange currency rates.",
            url=f"{HTTP_PROTOCOL}://{HTTP_HOST}:{HTTP_PORT}{HTTP_ROUTE}",
            preferred_transport=self.mode,
            additional_interfaces=[
                AgentInterface(
                    url=f"{HTTP_PROTOCOL}://{HTTP_HOST}:{HTTP_PORT}{HTTP_ROUTE}",
                    transport=self.mode,
                ),
            ],
            version="2.0.0",
            capabilities=AgentCapabilities(
                push_notifications=False,
                state_transition_history=False,
                streaming=streaming,
            ),
            default_input_modes=["text", "text/plain"],
            default_output_modes=["text", "text/plain"],
            skills=[self.agent_skill],
            supports_authenticated_extended_card=False,
        )
        self.agent_executor = A2aChatbotExecutor(streaming=streaming, blocking=blocking, strict=strict)

    def run(
        self,
        host: str = HTTP_HOST,
        port: int = HTTP_PORT,
    ) -> None:
        """Start HTTP Server."""
        server: A2AFastAPIApplication | A2ARESTFastAPIApplication
        if self.mode == "JSONRPC":
            server = A2AFastAPIApplication(
                agent_card=self.agent_card,
                http_handler=DefaultRequestHandler(
                    agent_executor=self.agent_executor,
                    task_store=InMemoryTaskStore(),
                ),
            )
        else:
            server = A2ARESTFastAPIApplication(
                agent_card=self.agent_card,
                http_handler=DefaultRequestHandler(
                    agent_executor=self.agent_executor,
                    task_store=InMemoryTaskStore(),
                ),
            )

        uvicorn.run(
            app=server.build(rpc_url=f"{HTTP_ROUTE}"),
            host=host,
            port=port,
        )
