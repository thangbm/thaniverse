"""The plan. Lives here, not in the transcript, and is re-injected every turn."""

MARKS = { "pending": "[]", "in_progress": "[~]", "done": "[x]"}
TODOS = [] # [{"task": "Example task", "activeForm": ..., "status": "pending"}]

def write_todos(todos: list[dict]):
    """Replace the whole list. Exactly one task may be in_progress at a time."""
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress, but only one is allowed."
    
    
    TODOS[:] = todos
    return todos_prompt() or "Todos list is empty."


def todos_prompt() -> str:
    return "\n".join(f"{MARKS[t['status']]} {t['task']}" for t in TODOS)


def active_form() -> str:
    """What the agent is doing right now, for the spinner."""
    for t in TODOS:
        if t["status"] == "in_progress":
            return t.get("activeForm")
    return "thinking"

TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a multi-step task. Send the whole list every time."
            "Keep exactly one task in progress at a time and update it as you go"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "The task description, imperative: 'Fix the parser'"},
                            "activeForm": {"type": "string", "description": "Present continuous form of the task, e.g., 'Fixing the parser'"},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "done"], "description": "The status of the task"}
                        },
                        "required": ["task", "activeForm", "status"]
                    },
                }
            },
            "required": ["todos"],
        },
    },
}