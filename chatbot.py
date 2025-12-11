"""
Name    : chatbot.py
Version : 1.0.0
Author  : aumezawa
"""
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from pprint import pprint
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

# Define State
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Define Node
def chatbot(state: State):
    return {
        "messages": [llm.invoke(state["messages"])]
    }

# Initialize Graph
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

# Execute
result = graph.invoke({"messages": ["こんにちは"]})

pprint(result)
