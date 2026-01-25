"""
a2a_chatbot.py

Version : 1.9.3
Author  : aumezawa
"""

from typing import Any, Literal, override

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AFastAPIApplication, A2ARESTFastAPIApplication
from a2a.server.events import EventQueue
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
from a2a.utils import new_task, new_text_artifact

from app.agents.chatbot import Chatbot
from app.tools.math import tools as math_tools

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
    ) -> None:
        """Initialize Chatbot Executor."""
        self.agent = Chatbot(
            tools=math_tools,
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

        try:
            # Streaming
            if self.streaming:
                task.status.state = TaskState.working
                await event_queue.enqueue_event(task)

                next_state = TaskState.completed
                async for event in await self.agent.astream_run(
                    query=quary,
                    thread_id=context.context_id,
                    resume=(task_state == TaskState.input_required),
                ):
                    if event.get("__interrupt__") is not None:
                        next_state = TaskState.input_required
                        break

                    if event.get("chatbot") is not None:
                        await event_queue.enqueue_event(
                            TaskArtifactUpdateEvent(
                                artifact=new_text_artifact(
                                    name="answer",
                                    text=event["chatbot"]["messages"][-1].content,
                                ),
                                context_id=task.context_id,
                                task_id=task.id,
                            ),
                        )

                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=next_state),
                        context_id=task.context_id,
                        task_id=task.id,
                        final=True,
                    ),
                )

            # Non-streaming
            else:
                if not self.blocking:
                    task.status.state = TaskState.working
                    task.artifacts = []
                    await event_queue.enqueue_event(task)

                last_event: dict[str, Any] = {}
                async for event in await self.agent.astream_run(
                    query=quary,
                    thread_id=context.context_id,
                    resume=(task_state == TaskState.input_required),
                ):
                    last_event = event

                if last_event.get("__interrupt__") is not None:
                    task.status.state = TaskState.input_required
                    task.artifacts = []
                    await event_queue.enqueue_event(task)

                if last_event.get("chatbot") is not None:
                    answer = last_event["chatbot"]["messages"][-1].content
                    task.status.state = TaskState.completed
                    task.artifacts = [new_text_artifact(name="answer", text=answer)]
                    await event_queue.enqueue_event(task)

        except Exception as e:  # noqa: BLE001
            task.status.state = TaskState.failed
            task.artifacts = []
            task.metadata = {"error": str(e)}
            await event_queue.enqueue_event(task)

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
    ) -> None:
        """Initialize A2A Chatbot."""
        self.mode = mode
        self.agent_skill = AgentSkill(
            id="calculating",
            name="calculating",
            description="A chatbot that can answer questions and perform calculations.",
            tags=["calculator"],
            input_modes=["text", "text/plain"],
            output_modes=["text", "text/plain"],
            examples=["100掛ける200を計算してください", "1足す2を計算してください"],
        )
        self.agent_card = AgentCard(
            name="Calculating_Chatbot",
            description="A chatbot that can answer questions and perform calculations.",
            url=f"{HTTP_PROTOCOL}://{HTTP_HOST}:{HTTP_PORT}{HTTP_ROUTE}",
            preferred_transport=self.mode,
            additional_interfaces=[
                AgentInterface(
                    url=f"{HTTP_PROTOCOL}://{HTTP_HOST}:{HTTP_PORT}{HTTP_ROUTE}",
                    transport=self.mode,
                ),
            ],
            version="1.9.3",
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
        self.agent_executor = A2aChatbotExecutor(streaming=streaming, blocking=blocking)

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
