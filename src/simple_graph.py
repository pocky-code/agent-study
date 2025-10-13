from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_aws import ChatBedrock
from langchain_core.tools import tool

class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]

@tool
def get_weather(city: str) -> str:
    """Get the current weather in a given city."""
    weather_map = {
        "New York": "sunny",
        "Los Angeles": "cloudy",
        "Chicago": "rainy"
    }
    return weather_map.get(city, "unknown")   

TOOLS = [get_weather]

llm = ChatBedrock(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-west-2",
    credentials_profile_name="pk",
    model_kwargs={
        "max_tokens": 4000,
        # "thinking": {"type": "enabled", "budget_tokens": 2000},
    },
)

llm_with_tools = llm.bind_tools(TOOLS)


def call_model(state: State) -> State:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(TOOLS) )
builder.add_conditional_edges("agent", tools_condition, ["tools", END])
builder.add_edge("tools", "agent")  # Loop back to agent after using tool
builder.add_edge(START, "agent")

graph = builder.compile()