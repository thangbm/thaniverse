import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

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
Always provide the most optimal solution and explain your reasoning if necessary.
Do not include any unnecessary commentary or information outside of the coding context.
Always focus on providing clear and concise code solutions.
Never include explanations that are not directly related to the code.
Always prioritize correctness and efficiency in your code solutions.
"""

BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run."
                }
            },
            "required": ["command"]
        },
    },
}

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
)
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