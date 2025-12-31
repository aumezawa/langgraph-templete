"""
chatbot.py

Version : 1.3.2
Author  : aumezawa
"""

from typing import Any, Annotated, TypedDict
from langgraph.graph.message import add_messages


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

    from langgraph.graph import START, END
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
    from langgraph.graph.state import CompiledStateGraph

    DEFAULT_LLM_MODEL = "gemini-2.5-flash"

    NODE_START = START
    NODE_SETUP = "setup"
    NODE_CHATBOT = "chatbot"
    NODE_TOOLS = "tools"
    NODE_END = END

    def __init__(
        self,
        model: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
        checkpointer: BaseCheckpointSaver[str] | None = None,
    ) -> None:
        """Initialize Chatbot."""
        from langgraph.checkpoint.memory import InMemorySaver
        from langchain_google_genai import ChatGoogleGenerativeAI

        self.model = model or ChatGoogleGenerativeAI(model=self.DEFAULT_LLM_MODEL)
        if tools:
            self.llm = self.model.bind_tools(tools)
        else:
            self.llm = self.model
        self.tools = tools or []
        self.checkpointer = checkpointer or InMemorySaver()
        self.graph = self._build_graph()

    def checkpoint(self, thread_id: str) -> Checkpoint | None:
        """Get Checkpointer."""
        from langchain_core.runnables import RunnableConfig

        return self.checkpointer.get(
            RunnableConfig(
                {
                    "configurable": {
                        "thread_id": thread_id,
                    },
                },
            ),
        )

    def _node_setup(self, state: ChatbotState) -> dict[str, list[Any]]:
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = [
            SystemMessage(content="英語で回答してください。"),
            HumanMessage(content=state["query"]),
        ]

        return {
            "messages": messages,
        }

    def _node_chatbot(self, state: ChatbotState) -> dict[str, list[Any]]:
        messages = [
            self.llm.invoke(state["messages"]),
        ]

        return {
            "messages": messages,
        }

    def _node_tools(self, state: ChatbotState) -> dict[str, list[Any]]:
        from langchain_core.messages import ToolMessage

        last_message = state["messages"][-1]
        messages = []
        for tool_call in last_message.tool_calls:
            for tool in self.tools:
                if tool_call["name"] == tool.name:
                    tool_output = tool.invoke(tool_call["args"])
                    tool_message = ToolMessage(
                        content=tool_output,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                    messages.append(tool_message)
        return {
            "messages": messages,
        }

    def _node_router(self, state: ChatbotState) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                if tool_call["name"] in [tool.name for tool in self.tools]:
                    return self.NODE_TOOLS
        return self.NODE_END

    def _build_graph(self) -> CompiledStateGraph[Any, None, Any, Any]:
        """Build Chatbot Graph."""
        from langgraph.graph import StateGraph

        # Initialize Graph
        builder = StateGraph(ChatbotState)

        builder.add_node(self.NODE_SETUP, self._node_setup)
        builder.add_node(self.NODE_CHATBOT, self._node_chatbot)
        builder.add_node(self.NODE_TOOLS, self._node_tools)

        builder.add_edge(self.NODE_START, self.NODE_SETUP)
        builder.add_edge(self.NODE_SETUP, self.NODE_CHATBOT)
        builder.add_conditional_edges(
            self.NODE_CHATBOT,
            self._node_router,
            {
                self.NODE_TOOLS: self.NODE_TOOLS,
                self.NODE_END: self.NODE_END,
            },
        )
        builder.add_edge(self.NODE_TOOLS, self.NODE_CHATBOT)

        return builder.compile(checkpointer=self.checkpointer)

    def run(self, query: str, thread_id: str | None = None) -> dict[str, Any]:
        """Run Chatbot."""
        from uuid import uuid4
        from langchain_core.runnables import RunnableConfig

        result = self.graph.invoke(
            input={
                "query": query,
            },
            config=RunnableConfig(
                {
                    "configurable": {
                        "thread_id": thread_id or uuid4().hex,
                    },
                },
            ),
        )

        if not isinstance(result, dict):
            return {}

        return result
