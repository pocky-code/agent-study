import json
from simple_graph import graph, State
from langchain.schema import HumanMessage

def lambda_handler(event):
    # 入力メッセージを取得
    body = event.get("body")
    if body:
        body = json.loads(body) 
    else:
        body = event

    user_message = body.get("message")
    if not user_message:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No message provided"})
        }
    # グラフを実行
    state = State(messages=[HumanMessage(content=user_message)])
    result = graph.invoke(state)
    # 結果メッセージを抽出
    messages = result.get("messages", [])
    response_message = messages[-1]["content"] if messages else ""

    return {
        "statusCode": 200,
        "body": json.dumps({"response": response_message})
    }