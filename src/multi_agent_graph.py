from datetime import date
from typing import Annotated, List, Literal, Optional, TypedDict

from langchain_aws import ChatBedrock
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

today = date.today().isoformat()


# =========================
# State
# =========================
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    route: Optional[
        Literal["weather", "web", "chat"]
    ]  # 分岐結果を保持（デバッグにも便利）


# =========================
# Tools
# =========================
REGISTERED_CITIES = {"New York": "sunny", "Los Angeles": "cloudy", "Chicago": "rainy"}


@tool
def get_weather(city: str) -> str:
    """Get weather for a registered city. Returns 'unknown' if not registered."""
    return REGISTERED_CITIES.get(city, "unknown")


# Tavily
web_search = TavilySearchResults(
    max_results=2,
    sarch_depth=1,
    include_answers=False,
    include_raw_content=False,
    include_images=False,
)

# agentごとに使うツールの束を分ける
WEATHER_TOOLS = [get_weather]
WEB_TOOLS = [web_search]


# =========================
# LLMs
# =========================
llm_base = ChatBedrock(
    # model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    # model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    model="us.amazon.nova-premier-v1:0",
    region="us-west-2",
    credentials_profile_name="pk",
    model_kwargs={"max_tokens": 2000},
)

# agentごとの LLM（ツール有無だけ変える）
llm_weather = llm_base.bind_tools(WEATHER_TOOLS)
llm_web = llm_base.bind_tools(WEB_TOOLS)
llm_chat = llm_base  # ツールなし


# =========================
# Router (構造化出力)
# =========================
class RouteSchema(BaseModel):
    route: Literal["weather", "web", "chat"] = Field(
        ..., description="weather | web | chat"
    )
    # Claudeに都市名/検索語の抽出もさせたいなら追加:
    city: Optional[str] = None
    query: Optional[str] = None


router = llm_base.with_structured_output(RouteSchema)


def classify(state: State):
    out = router.invoke(state["messages"])
    assert isinstance(out, RouteSchema)
    # ここでは route だけStateに保存（city/queryは各エージェントで再抽出でもOK）
    return {"route": out.route}


# =========================
# Agent nodes
# =========================
def weather_agent(state: State):
    """
    役割: まずは get_weather を呼ぶことを強く促す。
    未登録都市なら 'unknown' になり、ポストツールルーターで web-agent へ回す。
    """

    system = (
        f"You are a weather agent. Today's date is {today}. "
        "Prefer calling `get_weather` with the city explicitly. "
        "to clarify."
    )
    msgs = state["messages"] + [("system", system)]
    resp = llm_weather.invoke(msgs)
    return {"messages": [resp]}


def web_agent(state: State):
    """役割: Tavilyで検索して要約・出典を返す。"""
    system = (
        f"You are a web search agent. Today's date is {today}. "
        "Use `tavily_search_results_json` to find answers, "
        "then summarize with citations."
    )
    msgs = state["messages"] + [("system", system)]
    resp = llm_web.invoke(msgs)
    return {"messages": [resp]}


def chat_agent(state: State):
    """役割: 純チャット。"""
    system = "You are a helpful chat agent."
    msgs = state["messages"] + [("system", system)]
    resp = llm_chat.invoke(msgs)
    return {"messages": [resp]}


# =========================
# ToolNodes
# =========================
# weather_tools_node = ToolNode(WEATHER_TOOLS)
# web_tools_node = ToolNode(WEB_TOOLS)


# =========================
# Edge conditions
# =========================
def route_condition(state: State):
    r = state.get("route")
    if r == "weather":
        return "weather_agent"
    if r == "web":
        return "web_agent"
    return "chat_agent"


# tools_condition は「直前のAIメッセージにtool_callsがあるか」で tools / END を分岐
# weather_agent → (tools or END)
# web_agent → (tools or END)


def post_weather_tools(state: State):
    """
    Weather ToolNode の直後に呼ばれる分岐関数。
    直近の ToolMessage を見て、get_weather が 'unknown' なら web-agent にフォールバック。
    それ以外は weather_agent に戻して続ける（次の発話で終了判断）。
    """
    # 一番新しい ToolMessage を探す
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "get_weather":
            # get_weather の返答だけ見る（他はスルー）
            content = str(msg.content or "").strip().lower()
            if "unknown" in content:
                return "web_agent"  # ← 未登録都市 → web-agentへ
            break
    return "weather_agent"  # 既知の都市 or web_searchを使った直後など → 続行


# =========================
# Build Graph
# =========================
builder = StateGraph(State)

builder.add_node("classify", classify)
builder.add_node("weather_agent", weather_agent)
builder.add_node("web_agent", web_agent)
builder.add_node("chat_agent", chat_agent)

builder.add_node("weather_tools", ToolNode(WEATHER_TOOLS))
builder.add_node("web_tools", ToolNode(WEB_TOOLS))

# 入口
builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify", route_condition, ["weather_agent", "web_agent", "chat_agent"]
)

# weatherライン
builder.add_conditional_edges(
    "weather_agent", tools_condition, {"tools": "weather_tools", "__end__": END}
)
builder.add_conditional_edges(
    "weather_tools", post_weather_tools, ["web_agent", "weather_agent"]
)

# webライン
builder.add_conditional_edges(
    "web_agent", tools_condition, {"tools": "web_tools", "__end__": END}
)
builder.add_edge("web_tools", "web_agent")  # 続けて検索 → その後の発話でENDへ

# chatライン
builder.add_edge("chat_agent", END)

graph = builder.compile()
