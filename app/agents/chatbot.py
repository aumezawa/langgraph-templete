"""
chatbot.py

Version : 1.9.5
Author  : aumezawa
"""

import functools
from collections.abc import AsyncIterator
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt


###
# Define State
###
class ChatbotState(TypedDict):
    """Chatbot State Class."""

    query: str
    messages: Annotated[list[Any], add_messages]


###
# Define Chatbot Class
###
class Chatbot:
    """Chatbot Class."""

    DEFAULT_LLM_MODEL = "gemini-2.5-flash"

    NODE_START = START
    NODE_SETUP = "setup"
    NODE_CHATBOT = "chatbot"
    NODE_TOOLS = "tools"
    NODE_APPROVAL = "approval"
    NODE_END = END

    def __init__(
        self,
        model: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
        checkpointer: BaseCheckpointSaver[str] | None = None,
        system_prompt: str = "Answer in Japanese.",
    ) -> None:
        """Initialize Chatbot."""
        self.model = model or ChatGoogleGenerativeAI(model=self.DEFAULT_LLM_MODEL)
        if tools:
            self.llm = self.model.bind_tools(tools)
        else:
            self.llm = self.model
        self.tools = tools or []
        self.checkpointer = checkpointer or InMemorySaver()
        self.system_prompt = system_prompt
        self.graph = self._build_graph(self.llm)

    def checkpoint(self, thread_id: str) -> Checkpoint | None:
        """Get Checkpointer."""
        return self.checkpointer.get(
            RunnableConfig(
                {
                    "configurable": {
                        "thread_id": thread_id,
                    },
                },
            ),
        )

    def _build_graph(self, llm: Runnable[Any, Any] | None = None) -> CompiledStateGraph[Any, None, Any, Any]:
        """Build Chatbot Graph."""
        # Initialize Graph
        builder = StateGraph(ChatbotState)

        def _node_setup(state: ChatbotState) -> dict[str, list[Any]]:
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=state["query"]),
            ]

            return {
                "messages": messages,
            }

        def _node_chatbot(state: ChatbotState, llm: Runnable[Any, Any]) -> dict[str, list[Any]]:
            messages = [
                llm.invoke(state["messages"]),
            ]

            return {
                "messages": messages,
            }

        def _node_router(state: ChatbotState) -> str:
            last_message = state["messages"][-1]
            if last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    if tool_call["name"] in [tool.name for tool in self.tools]:
                        return self.NODE_APPROVAL
            return self.NODE_END

        def _node_approval(state: ChatbotState) -> dict[str, list[Any]]:  # noqa: ARG001
            approval = interrupt("Do you approve using an external tool? [yes/no]")

            messages = []
            if str(approval).upper() == "NO":
                messages.append(HumanMessage(content="Don't use any external tools."))

            return {
                "messages": messages,
            }

        builder.add_node(self.NODE_SETUP, _node_setup)
        builder.add_node(self.NODE_CHATBOT, functools.partial(_node_chatbot, llm=(llm or self.llm)))
        builder.add_node(self.NODE_TOOLS, ToolNode(self.tools))
        builder.add_node(self.NODE_APPROVAL, _node_approval)

        builder.add_edge(self.NODE_START, self.NODE_SETUP)
        builder.add_edge(self.NODE_SETUP, self.NODE_CHATBOT)
        builder.add_conditional_edges(self.NODE_CHATBOT, _node_router)
        builder.add_edge(self.NODE_APPROVAL, self.NODE_TOOLS)
        builder.add_edge(self.NODE_TOOLS, self.NODE_CHATBOT)

        return builder.compile(checkpointer=self.checkpointer)

    async def async_run(
        self,
        query: str,
        *,
        thread_id: str | None = None,
        llm: Runnable[Any, Any] | None = None,
        raw_output: bool = False,
    ) -> str | dict[str, Any]:
        """Run Chatbot."""
        if llm:
            self.graph = self._build_graph(llm)
        elif not hasattr(self, "graph"):
            self.graph = self._build_graph(self.llm)

        result = await self.graph.ainvoke(
            input={
                "query": query,
            },
            config=RunnableConfig(
                {
                    "configurable": {
                        "thread_id": thread_id or str(uuid4()),
                    },
                },
            ),
        )

        if raw_output:
            return result

        content = result.get("messages", [])[-1].content
        return (
            content
            if isinstance(content, str)
            else " ".join(
                [str(chunk) if isinstance(chunk, str) else chunk.get("text", "") for chunk in content],
            )
        )

    async def astream_run(
        self,
        query: str,
        *,
        thread_id: str | None = None,
        resume: bool = False,
        llm: Runnable[Any, Any] | None = None,
        raw_output: bool = False,
    ) -> AsyncIterator[tuple[str | dict[str, Any], bool]]:
        """Run Chatbot."""
        if llm:
            self.graph = self._build_graph(llm)
        elif not hasattr(self, "graph"):
            self.graph = self._build_graph(self.llm)

        async for event in self.graph.astream(
            input={"query": query} if not resume else Command(resume=query),
            config=RunnableConfig(
                {
                    "configurable": {
                        "thread_id": thread_id or str(uuid4()),
                    },
                },
            ),
        ):
            if raw_output:
                yield (event, bool(event.get("__interrupt__")))
                continue

            if event.get("__interrupt__") is not None:
                yield (event.get("__interrupt__", [])[0].value, True)
                continue

            messages = next(iter(event.values())).get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                content = messages[-1].content
                if not content:
                    continue
                elif isinstance(content, str):
                    yield (content, False)
                else:
                    yield (
                        " ".join(
                            [chunk if isinstance(chunk, str) else chunk.get("text", "") for chunk in content],
                        ),
                        False,
                    )
