import os

from dotenv import load_dotenv
from openai import OpenAI

from py_core.tools import TOOL_SCHEMAS

load_dotenv()
model_name = os.getenv("MODEL_NAME")

client = OpenAI(
    base_url = os.getenv("MODEL_BASE_URL"),
    api_key = os.getenv("MODEL_API_KEY")
)

# user_input = input("Enter your prompt: ")
SYSTEM_PROMPT = """
You are a coding agent. Your job is to code efficiently and accurately based on the user's prompts.
Use the bash tool to inspect files.
Answer back to the user one exploration is done.
"""


# response = client.chat.completions.create(
#     model=model_name,
#     messages=[
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": user_input}
#     ],
#     tools=TOOL_SCHEMAS
# )
# # breakpoint()
# output = response.choices[0].message.content
# completion_details = response.usage.completion_tokens_details
# prompt_details = response.usage.prompt_tokens_details

# usage = {
#     "prompt_tokens": response.usage.prompt_tokens,
#     "completion_tokens": response.usage.completion_tokens,
#     "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
#     "cached_tokens": getattr(prompt_details, "cached_tokens", None)
# }

# print("Output:\n", output)
# print("Usage:\n", usage)

def call_llm(messages):
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=TOOL_SCHEMAS
    )

    message = response.choices[0].message
    completion_details = response.usage.completion_tokens_details
    prompt_details = response.usage.prompt_tokens_details

    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None)
    }

    return message, usage

# if __name__ == "__main__":
#     user_input = input("Enter your prompt> ")

#     message, usage = call_llm([
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": user_input},
#     ])

#     print("\nAgent: ", message.content, "\n")

#     if message.tool_calls:
#         tool_call = message.tool_calls[0]
#         args = json.loads(tool_call.function.arguments)
#         result = TOOLS[tool_call.function.name](**args)
#         print("Tool: ", tool_call.function.name, args)
#         print(result, "\n")

#     print(usage)