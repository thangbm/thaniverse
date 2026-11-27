from pathlib import Path
import shutil
import sys
from typing import List, Optional
import subprocess
import tempfile

PROJECT = Path.cwd().resolve()

PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""

def wrap(command: str) -> Optional[List[str]]:
    """Wrap a shell command in an OS sandbox. None means we have no sandbox available."""
    if sys.platform == "darwin":
        profile = Path(tempfile.gettempdir()) / "thaniverse.sb"
        profile.write_text(PROFILE)
        return ["sandbox-exec", "-f", str(profile), "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind", "/", "/",
            "--bind", str(PROJECT), str(PROJECT),
            "--dev", "/dev", "--proc", "/proc",
            "--unshare-net", "--die-with-parent",
            "/bin/sh", "-c", command,
        ]
    
    if sys.platform == "win32":
        # No sandbox CLI ships with Windows, so our own launcher starts the
        # command in an AppContainer (see win_sandbox.py).
        launcher = Path(__file__).with_name("win_sandbox.py")
        return [sys.executable, str(launcher), str(PROJECT), command]

    return None # Linux without bubblewrap (bwrap)

def name():
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )