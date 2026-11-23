import subprocess

def bash(command: str):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def read_file(path: str) -> str:
    """Read the contents of a file and return it as a string."""
    with open(path, "r") as f:
        return f.read()

TOOL_SCHEMAS = [{
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
}, {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file and return it as a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read."
                }
            },
            "required": ["path"]
        },
    },
}]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    # "write_file": write_file,
    # "str_replace": str_replace,
    # "read_skill": read_skill,
    # "write_todos": write_todos,
    # "task": task,
}