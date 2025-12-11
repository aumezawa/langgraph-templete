"""
Name    : chatbot.py
Version : 1.1.0
Author  : aumezawa
"""
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from pprint import pprint
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

NODE_START = START
NODE_CHATBOT = "chatbot"
NODE_TOOLS = "tools"
NODE_ROUTER = "router"
NODE_END = END

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

# Setup LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)
llm_with_tools = llm.bind_tools(list(tools_dict.values()))

# Define State
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Define Node
def chatbot(state: State):
    return {
        "messages": [llm_with_tools.invoke(state["messages"])]
    }

def tools(state: State):
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
graph_builder = StateGraph(State)

graph_builder.add_node(NODE_CHATBOT, chatbot)
graph_builder.add_node(NODE_TOOLS, tools)

graph_builder.add_edge(NODE_START, NODE_CHATBOT)
graph_builder.add_conditional_edges(
    NODE_CHATBOT,
    router,
    {
        NODE_TOOLS: NODE_TOOLS,
        NODE_END: NODE_END
    }
)
graph_builder.add_edge(NODE_TOOLS, NODE_CHATBOT)

graph = graph_builder.compile()

# Execute
result = graph.invoke({
    "messages": ["100掛ける200の計算と1足す2の計算をそれぞれしてください"]
})

pprint(result)
