from typing import Annotated, List, TypedDict

from langchain_aws import ChatBedrock
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import os


# ---------- State ----------
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


# ---------- Tools ----------
@tool
def get_weather(city: str) -> str:
    """Get the current weather in a given city."""
    weather_map = {"New York": "sunny", "Los Angeles": "cloudy", "Chicago": "rainy"}
    return weather_map.get(city, "unknown")


web_search = TavilySearchResults(max_results=2)

TOOLS = [get_weather, web_search]

# ---------- LLM ----------
llm = ChatBedrock(
    model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region="us-west-2",
    credentials_profile_name=None if os.getenv("AWS_EXECUTION_ENV") else "pk",
    model_kwargs={
        "max_tokens": 4000,
        # "thinking": {"type": "enabled", "budget_tokens": 2000},
    },
)

llm_with_tools = llm.bind_tools(TOOLS)


def call_model(state: State):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_conditional_edges("agent", tools_condition, ["tools", END])
builder.add_edge("tools", "agent")  # Loop back to agent after using tool
builder.add_edge(START, "agent")

graph = builder.compile()
