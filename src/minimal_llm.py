from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatBedrock(
    model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region="us-west-2",
    credentials_profile_name="pk",
    model_kwargs={
        "max_tokens": 4000,
        "thinking": {"type": "enabled", "budget_tokens": 2000},
    },
)

prompt = "Write a poem about the moon."
# response = llm.invoke([HumanMessage(content=prompt)])
# print(response.additional_kwargs["thinking"]["text"])
# print(response.content)


messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content=prompt),
]

for chunk in llm.stream(messages):
    # Each chunk.content is likely a list of dicts
    for item in chunk.content:
        if isinstance(item, dict):
            if item.get("type") == "thinking":
                # Print thinking text as it streams
                print(item.get("thinking", ""), end="", flush=True)
            elif item.get("type") == "text":
                # Stream output text token by token
                text = item.get("text", "")
                for token in text:
                    print(token, end="", flush=True)
        else:
            print(item, end="", flush=True)


print()  # Newline after thinking and output
