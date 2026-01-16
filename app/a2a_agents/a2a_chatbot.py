"""
a2a_chatbot.py

Version : 1.5.0
Author  : aumezawa
"""

from typing import override, Literal
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue


HTTP_PROTOCOL: Literal["http", "https"] = "http"
HTTP_HOST: str = "localhost"
HTTP_PORT: int = 8000
HTTP_ROUTE: str = "/a2a/chatbot"


class A2aChatbotExecutor(AgentExecutor):
    """A2A Chatbot Executor Class."""

    def __init__(
        self,
    ) -> None:
        """Initialize Chatbot Executor."""
        from app.agents.chatbot import Chatbot
        from app.tools.math import tools as math_tools

        self.agent = Chatbot(
            tools=math_tools,
        )

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute Agent."""
        from a2a.utils import new_agent_text_message

        result = await self.agent.async_run(
            query=context.get_user_input(),
            thread_id=context.context_id,
        )
        message = result["messages"][-1].content
        await event_queue.enqueue_event(new_agent_text_message(message))

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
        mode: Literal["JSONRPC", "GRPC", "HTTP+JSON"] = "HTTP+JSON",
    ) -> None:
        """Initialize A2A Chatbot."""
        from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

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
            version="1.5.0",
            capabilities=AgentCapabilities(
                push_notifications=False,
                state_transition_history=False,
                streaming=False,
            ),
            default_input_modes=["text", "text/plain"],
            default_output_modes=["text", "text/plain"],
            skills=[self.agent_skill],
            supports_authenticated_extended_card=False,
        )
        self.agent_executor = A2aChatbotExecutor()

    def run(
        self,
        host: str = HTTP_HOST,
        port: int = HTTP_PORT,
    ) -> None:
        """Start HTTP Server."""
        import uvicorn
        from a2a.server.apps import A2AFastAPIApplication, A2ARESTFastAPIApplication
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import InMemoryTaskStore

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
