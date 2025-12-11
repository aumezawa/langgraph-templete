"""
Name    : chatbot.py
Version : 1.1.1
Author  : aumezawa
"""
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from pprint import pprint
from langchain_core.tools import tool, Tool, BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

# Set API Key
load_dotenv()

# Define Tools
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
    "add_function": add_function
}

# Generate Chatbot Graph
def chatbot_builder(*, model: BaseChatModel, tools: Sequence[BaseTool | Tool]):
    from langchain_core.messages import ToolMessage
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages

    # Setup LLM
    llm = model.bind_tools(tools)

    # Define State
    class State(TypedDict):
        messages: Annotated[list, add_messages]

    # Define Node
    NODE_START = START
    NODE_CHATBOT = "chatbot"
    NODE_TOOLS = "tools"
    NODE_END = END

    def node_chatbot(state: State):
        return {
            "messages": [llm.invoke(state["messages"])]
        }

    def node_tools(state: State):
        last_message = state["messages"][-1]
        messages = []
        for tool_call in last_message.tool_calls:
            tool_output = tools_dict[tool_call["name"]].invoke(tool_call["args"])
            tool_messages = ToolMessage(
                content=tool_output,
                name=tool_call["name"],
                tool_call_id=tool_call["id"]
            )
            messages.append(tool_messages)
        #
        return {
            "messages": messages
        }

    # Define Router
    def router(state: State):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return NODE_TOOLS
        else:
            return NODE_END

    # Initialize Graph
    builder = StateGraph(State)

    builder.add_node(NODE_CHATBOT, node_chatbot)
    builder.add_node(NODE_TOOLS, node_tools)

    builder.add_edge(NODE_START, NODE_CHATBOT)
    builder.add_conditional_edges(
        NODE_CHATBOT,
        router,
        {
            NODE_TOOLS: NODE_TOOLS,
            NODE_END: NODE_END
        }
    )
    builder.add_edge(NODE_TOOLS, NODE_CHATBOT)

    return builder.compile()

# Main Function
def main():
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash"
    )

    graph = chatbot_builder(
        model=model,
        tools=list(tools_dict.values())
    )

    # Execute
    result = graph.invoke({
        "messages": ["100掛ける200の計算と1足す2の計算をそれぞれしてください"]
    })

    pprint(result)
    return

if __name__ == "__main__":
    main()
