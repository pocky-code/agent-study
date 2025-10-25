import json
import logging

from langchain.schema import HumanMessage

from .simple_graph import State, graph

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, _context):
    logger.info(f"Received event: {event}")

    # 入力メッセージを取得
    body = event.get("body")
    logger.info(f"Raw body: {body}")

    body = json.loads(body) if body else event
    logger.info(f"Parsed body: {body}")

    user_message = body.get("message")
    logger.info(f"User message: {user_message}")

    if not user_message:
        logger.warning("No message provided in the request.")
        return {"statusCode": 400, "body": json.dumps({"error": "No message provided"})}

    # グラフを実行
    state = State(messages=[HumanMessage(content=user_message)])
    logger.info(f"Initial state: {state}")

    result = graph.invoke(state)
    logger.info(f"Graph result: {result}")

    # 結果メッセージを抽出
    messages = result.get("messages", [])
    logger.info(f"Result messages: {messages}")

    response_message = messages[-1].content if messages else ""
    logger.info(f"Response message: {response_message}")

    response = {"statusCode": 200, "body": json.dumps({"response": response_message})}
    logger.info(f"Returning response: {response}")

    return response
