import json
from py_core.tools import TOOLS
from factory.cli.llm import call_llm, SYSTEM_PROMPT
from py_core.context import reminder

user_input = input("Enter your prompt> ")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input}
]

while True:
    message, usage = call_llm(messages + [reminder()])

    messages.append(message.model_dump(exclude_none=True))

    if (message.content):
        print("\nAgent: ", message.content, "\n")

    if not message.tool_calls:
        break

    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        print("Tool: ", tool_call.function.name, args)
        print(result, "\n")

        messages.append({
            "role": "tool",
            "name": tool_call.function.name,
            "tool_call_id": tool_call.id,
            "content": result
        })

    print("Usage:\n", usage)

# if message.tool_calls:
#     tool_call = message.tool_calls[0]
#     args = json.loads(tool_call.function.arguments)
#     result = TOOLS[tool_call.function.name](**args)
#     print("Tool: ", tool_call.function.name, args)
#     print(result, "\n")

# print(usage)