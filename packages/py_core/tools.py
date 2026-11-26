import subprocess

from py_core.context import note_read

def bash(command: str):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def read_file(path: str) -> str:
    """Read the contents of a file and return it as a string."""
    note_read(path)
    with open(path, "r") as f:
        return f.read()

def write_file(path: str, content: str):
    """Create a file, or write the given content to a file at the specified path."""
    with open(path, "w") as f:
        f.write(content)

    return f"Wrote to {path}"

def str_replace(path: str, old: str, new: str, allow_multi_edit: bool = False) -> str:
    """Replace occurrences of 'old' with 'new' in 'text'. If 'allow_multi_edit' is False, only replace the first occurrence."""
    with open(path, "r") as f:
        content = f.read()

    count = content.count(old)
    if count == 0:
        return f"Error: No occurrences of '{old}' found in {path}"

    if count > 1 and not allow_multi_edit:
        return f"Error: Multiple occurrences of '{old}' found in {path}, but 'allow_multi_edit' is False."
    
    with open(path, "w") as f:
        f.write(content.replace(old, new))

    return f"Replaced '{old}' with '{new}' in {path}"

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
}, {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file at the specified path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to write to."
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file."
                }
            },
            "required": ["path", "content"]
        },
    },
}, {
    "type": "function",
    "function": {
        "name": "str_replace",
        "description": "Replace occurrences of a string in a file with a new string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to perform the replacement in."
                },
                "old": {
                    "type": "string",
                    "description": "The string to be replaced."
                },
                "new": {
                    "type": "string",
                    "description": "The string to replace with."
                }
            },
            "required": ["path", "old", "new"]
        },
    },
}]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    # "read_skill": read_skill,
    # "write_todos": write_todos,
    # "task": task,
}