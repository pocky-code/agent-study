from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str

def to_upper(state: State) -> State:
    return {"text": state["text"].upper()}

builder = StateGraph(State)
builder.add_node("to_upper", to_upper)
builder.add_edge(START, "to_upper")
builder.add_edge("to_upper", END)  

graph = builder.compile()