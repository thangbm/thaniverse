import os
import subprocess

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_SCHEMAS

load_dotenv()
model_name = os.getenv("MODEL_NAME")

client = OpenAI(
    base_url = os.getenv("MODEL_BASE_URL"),
    api_key = os.getenv("MODEL_API_KEY")
)

user_input = input("Enter your prompt: ")
SYSTEM_PROMPT = """
You are a coding agent. Your job is to code efficiently and accurately based on the user's prompts.
Use the bash tool to inspect files.
Answer back to the user one exploration is done.
"""

# def bash(command: str):
#     result = subprocess.run(command, shell=True, capture_output=True, text=True)
#     return result.stdout + result.stderr

# def read_file(path: str) -> str:
#     """Read the contents of a file and return it as a string."""
#     with open(path, "r") as f:
#         return f.read()

# TOOL_SCHEMAS = [{
#     "type": "function",
#     "function": {
#         "name": "bash",
#         "description": "Run a shell command and return its output.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "command": {
#                     "type": "string",
#                     "description": "The shell command to run."
#                 }
#             },
#             "required": ["command"]
#         },
#     },
# }, {
#     "type": "function",
#     "function": {
#         "name": "read_file",
#         "description": "Read the contents of a file and return it as a string.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "path": {
#                     "type": "string",
#                     "description": "The path to the file to read."
#                 }
#             },
#             "required": ["path"]
#         },
#     },
# }]


response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ],
    tools=TOOL_SCHEMAS
)
breakpoint()
output = response.choices[0].message.content
completion_details = response.usage.completion_tokens_details
prompt_details = response.usage.prompt_tokens_details

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
    "cached_tokens": getattr(prompt_details, "cached_tokens", None)
}

print("Output:\n", output)
print("Usage:\n", usage)