"""
chatbot.py

Version : 1.3.0
Author  : aumezawa
"""

from typing import Any, Annotated, TypedDict
from collections.abc import Sequence
from dotenv import load_dotenv
from pprint import pprint
from langchain_core.tools import tool, Tool, BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.types import Checkpointer
from langgraph.graph.state import CompiledStateGraph

###
# Set API Key
###
load_dotenv()


###
# Define Tools
###
@tool
def multiply_function(x: int, y: int) -> int:
    """
    2つのint型の値を引数で受け取り、掛け算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x * y
    """
    return x * y


@tool
def add_function(x: int, y: int) -> int:
    """
    2つのint型の値を引数で受け取り、足し算の結果をint型で返す

    Args:
        x (int): 1つ目のint型の引数
        y (int): 2つ目のint型の引数

    Returns:
        int: x + y
    """
    return x + y


tools_dict = {
    "multiply_function": multiply_function,
    "add_function": add_function,
}


###
# Generate Chatbot Graph
###
def chatbot_builder(
    *,
    model: BaseChatModel,
    tools: Sequence[BaseTool | Tool],
    checkpointer: Checkpointer = None,
) -> CompiledStateGraph[Any, None, Any, Any]:
    """Create a chatbot graph with tool usage capability."""
    from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages

    # Define Node
    node_start = START
    node_system = "system"
    node_chatbot = "chatbot"
    node_tools = "tools"
    node_end = END

    # Setup LLM
    llm = model.bind_tools(tools)

    # Define State
    class State(TypedDict):
        query: str
        messages: Annotated[list[Any], add_messages]

    def act_system(state: State) -> dict[str, list[Any]]:
        messages: list[Any] = []

        system_message = SystemMessage(content="英語で回答してください。")

        user_message = HumanMessage(content=state["query"])

        messages.append(system_message)
        messages.append(user_message)

        return {
            "messages": messages,
        }

    def act_chatbot(state: State) -> dict[str, list[Any]]:
        messages = []
        ai_message = llm.invoke(state["messages"])
        messages.append(ai_message)

        return {
            "messages": messages,
        }

    def act_tools(state: State) -> dict[str, list[Any]]:
        last_message = state["messages"][-1]
        messages = []
        for tool_call in last_message.tool_calls:
            tool_output = tools_dict[tool_call["name"]].invoke(tool_call["args"])
            tool_message = ToolMessage(
                content=tool_output,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
            messages.append(tool_message)

        return {
            "messages": messages,
        }

    # Define Router
    def router(state: State) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return node_tools
        return node_end

    # Initialize Graph
    builder = StateGraph(State)

    builder.add_node(node_system, act_system)
    builder.add_node(node_chatbot, act_chatbot)
    builder.add_node(node_tools, act_tools)

    builder.add_edge(node_start, node_system)
    builder.add_edge(node_system, node_chatbot)
    builder.add_conditional_edges(
        node_chatbot,
        router,
        {
            node_tools: node_tools,
            node_end: node_end,
        },
    )
    builder.add_edge(node_tools, node_chatbot)

    return builder.compile(checkpointer=checkpointer)


###
# Main Function
###
def main() -> None:
    """Execute main function."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.checkpoint.memory import InMemorySaver

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
    )

    checkpointer = InMemorySaver()

    config = RunnableConfig(
        {
            "configurable": {
                "thread_id": "chatbot_example_thread",
            },
        },
    )

    graph = chatbot_builder(
        model=model,
        tools=list(tools_dict.values()),
        checkpointer=checkpointer,
    )

    # Execute
    result = graph.invoke(
        input={
            "query": "100掛ける200の計算と1足す2の計算をそれぞれしてください",
        },
        config=config,
    )

    print("=== Result ===")
    pprint(result)
    print("=== Checkpointer ===")
    print(checkpointer.get(config))


if __name__ == "__main__":
    main()
