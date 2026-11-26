import subprocess
import os
from datetime import datetime

SEEN = {} # path -> mtime when the agent last read it

def note_read(path: str) -> str:
    SEEN[path] = os.path.getmtime(path)

def stale_files() -> list[str]:
    """Return a list of files that have changed since they were last read."""
    return [path for path, mtime in SEEN.items() if os.path.getmtime(path) != mtime]

def git_branch() -> str:
    result = subprocess.run(
        "git branch --show-current", shell=True, capture_output=True, text=True
    )
    return result.stdout.strip() or "(detached)"

def reminder() -> str:
    """The block we append to the messages on every turn."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"git branch: {git_branch()}\n"
            "</env>"
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

