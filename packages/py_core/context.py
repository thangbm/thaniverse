import hashlib
import subprocess
import os
from datetime import datetime
from pathlib import Path
from py_core.todo import todos_prompt

SEEN = {} # path -> mtime when the agent last read it
LABELS = {"M": "modified", "D": "deleted", "A": "added", "??": "new"}

def note_read(path: str) -> str:
    SEEN[path] = os.path.getmtime(path)

def stale_files() -> list[str]:
    """Return a list of files that have changed since they were last read."""
    return [path for path, mtime in SEEN.items() if os.path.getmtime(path) != mtime]

def git_state():
    """path -> (status, content hash) for every file git sees as changed."""
    state = {}
    for line in git("status --porcelain").splitlines():
        path = line[3:]
        state[path] = (line[:2].strip(), file_hash(path))
    return state

def file_hash(path):
    file = Path(path)
    return hashlib.md5(file.read_bytes()).hexdigest() if file.is_file() else None

def git(command: str) -> str:
    result = subprocess.run(
        f"git {command}", shell=True, capture_output=True, text=True
    )
    return result.stdout

LAST_STATE = git_state()

def file_changes():
    """Files whose status of contents moved since the previous turn."""
    global LAST_STATE
    now = git_state()
    changed = {p: v[0] for p, v in now.items() if LAST_STATE.get(p) != v}
    LAST_STATE = now
    return changed

def changes_note():
    changed = file_changes()
    if not changed:
        return ""
    lines = [f"{LABELS.get(code, code)}: {path}" for path, code in changed.items()]
    return (
        "\n<system-reminder>\n"
        "These files changed since your last turn. Read them again before "
        "editing:\n" + "\n".join(lines) + "\n</system-reminder>"
    )

def todos_note() -> str:
    plan = todos_prompt()
    return (
        f"\n<todos>\n{plan}\n</todos>" if plan else ""
    )

def reminder() -> str:
    """The block we append to the messages on every turn."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"git branch: {git('branch --show-current').strip() or '(detached)'}\n"
            "</env>" + todos_note() + changes_note()
        )
    }

def stale_note() -> str:
    """Warn about files that changed on disk since the agent read them."""
    stale = stale_files()
    if not stale:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed on disk since they were last read. Read them "
        "again before editing: \n" + "\n".join(stale) +"\n</system-reminder>"
    )

