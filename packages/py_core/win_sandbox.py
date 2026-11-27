"""Run a shell command inside a Windows AppContainer.

Usage: python win_sandbox.py <project dir> <command>

The AppContainer is Windows' own sandbox (the one UWP apps run in):
- no network, because we grant it no capabilities (no internetClient);
- it can write only where an ACL grants its SID access, so we grant it the
  project folder, but only read access to the project's .git folder;
- it can read system folders (Windows, Program Files), but not the rest of
  the user profile.
- the command dies with this launcher (job object), like bwrap's --die-with-parent.

Only the standard library is used, so it runs as a plain script.
"""
import ctypes
import os
import subprocess
import sys
from ctypes import wintypes as w
from pathlib import Path

NAME = "thaniverse.sandbox"
ALREADY_EXISTS = 0x800700B7  # HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS)

EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_SUSPENDED = 0x00000004
CREATE_UNICODE_ENVIRONMENT = 0x00000400
STARTF_USESTDHANDLES = 0x00000100
HANDLE_FLAG_INHERIT = 0x00000001
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9
INFINITE = 0xFFFFFFFF

userenv = ctypes.WinDLL("userenv")
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ole32 = ctypes.WinDLL("ole32")


class SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.c_void_p),
        ("CapabilityCount", w.DWORD),
        ("Reserved", w.DWORD),
    ]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR),
        ("lpTitle", w.LPWSTR), ("dwX", w.DWORD), ("dwY", w.DWORD),
        ("dwXSize", w.DWORD), ("dwYSize", w.DWORD), ("dwXCountChars", w.DWORD),
        ("dwYCountChars", w.DWORD), ("dwFillAttribute", w.DWORD),
        ("dwFlags", w.DWORD), ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
        ("lpReserved2", ctypes.c_void_p), ("hStdInput", w.HANDLE),
        ("hStdOutput", w.HANDLE), ("hStdError", w.HANDLE),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", w.HANDLE), ("hThread", w.HANDLE),
        ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", w.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", w.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", w.DWORD),
        ("SchedulingClass", w.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", ctypes.c_uint64 * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _sig(fn, restype, *argtypes):
    fn.restype, fn.argtypes = restype, list(argtypes)


P = ctypes.POINTER
_sig(userenv.CreateAppContainerProfile, ctypes.c_long,
     w.LPCWSTR, w.LPCWSTR, w.LPCWSTR, ctypes.c_void_p, w.DWORD, P(ctypes.c_void_p))
_sig(userenv.DeriveAppContainerSidFromAppContainerName, ctypes.c_long,
     w.LPCWSTR, P(ctypes.c_void_p))
_sig(userenv.GetAppContainerFolderPath, ctypes.c_long, w.LPCWSTR, P(ctypes.c_void_p))
_sig(advapi32.ConvertSidToStringSidW, w.BOOL, ctypes.c_void_p, P(ctypes.c_void_p))
_sig(kernel32.LocalFree, ctypes.c_void_p, ctypes.c_void_p)
_sig(ole32.CoTaskMemFree, None, ctypes.c_void_p)
_sig(kernel32.GetStdHandle, w.HANDLE, w.DWORD)
_sig(kernel32.SetHandleInformation, w.BOOL, w.HANDLE, w.DWORD, w.DWORD)
_sig(kernel32.InitializeProcThreadAttributeList, w.BOOL,
     ctypes.c_void_p, w.DWORD, w.DWORD, P(ctypes.c_size_t))
_sig(kernel32.UpdateProcThreadAttribute, w.BOOL, ctypes.c_void_p, w.DWORD,
     ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p)
_sig(kernel32.DeleteProcThreadAttributeList, None, ctypes.c_void_p)
_sig(kernel32.CreateProcessW, w.BOOL, w.LPCWSTR, w.LPWSTR, ctypes.c_void_p,
     ctypes.c_void_p, w.BOOL, w.DWORD, ctypes.c_void_p, w.LPCWSTR,
     ctypes.c_void_p, ctypes.c_void_p)
_sig(kernel32.CreateJobObjectW, w.HANDLE, ctypes.c_void_p, w.LPCWSTR)
_sig(kernel32.SetInformationJobObject, w.BOOL, w.HANDLE, ctypes.c_int,
     ctypes.c_void_p, w.DWORD)
_sig(kernel32.AssignProcessToJobObject, w.BOOL, w.HANDLE, w.HANDLE)
_sig(kernel32.ResumeThread, w.DWORD, w.HANDLE)
_sig(kernel32.WaitForSingleObject, w.DWORD, w.HANDLE, w.DWORD)
_sig(kernel32.GetExitCodeProcess, w.BOOL, w.HANDLE, P(w.DWORD))
_sig(kernel32.CloseHandle, w.BOOL, w.HANDLE)


def _check(ok):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())


def _check_hr(hr, what):
    if hr != 0:
        raise OSError(f"{what} failed: HRESULT 0x{hr & 0xFFFFFFFF:08X}")


def container_sid() -> ctypes.c_void_p:
    """The SID of our AppContainer profile, creating the profile on first use."""
    sid = ctypes.c_void_p()
    hr = userenv.CreateAppContainerProfile(
        NAME, NAME, "Thaniverse agent sandbox", None, 0, ctypes.byref(sid))
    if hr & 0xFFFFFFFF == ALREADY_EXISTS:
        hr = userenv.DeriveAppContainerSidFromAppContainerName(NAME, ctypes.byref(sid))
    _check_hr(hr, "AppContainer profile")
    return sid


def sid_string(sid) -> str:
    out = ctypes.c_void_p()
    _check(advapi32.ConvertSidToStringSidW(sid, ctypes.byref(out)))
    try:
        return ctypes.wstring_at(out.value)
    finally:
        kernel32.LocalFree(out)


def container_folder(sid_str: str) -> Path:
    """%LOCALAPPDATA%\\Packages\\<name>\\AC: the one place the container may always write."""
    out = ctypes.c_void_p()
    _check_hr(userenv.GetAppContainerFolderPath(sid_str, ctypes.byref(out)),
              "GetAppContainerFolderPath")
    try:
        return Path(ctypes.wstring_at(out.value))
    finally:
        ole32.CoTaskMemFree(out)


def grant(project: Path, sid_str: str, folder: Path):
    """Let the container modify the project, but not its .git folder.

    Rewriting ACLs walks the whole tree, so we remember which projects are done.
    """
    marker = folder / "granted.txt"
    done = marker.read_text("utf-8").splitlines() if marker.exists() else []
    if str(project) in done:
        return
    quiet = {"check": True, "stdout": subprocess.DEVNULL}
    subprocess.run(["icacls", str(project), "/grant", f"*{sid_str}:(OI)(CI)M", "/Q"], **quiet)
    git = project / ".git"
    if git.exists():
        # Windows ignores deny ACEs for an AppContainer SID, so .git instead stops
        # inheriting from the project (/inheritance:d keeps a copy of the inherited
        # ACEs) and the container's copy is replaced by read-only access.
        for args in (["/inheritance:d"], ["/remove:g", f"*{sid_str}"],
                     ["/grant", f"*{sid_str}:(OI)(CI)RX"]):
            subprocess.run(["icacls", str(git), *args, "/Q"], **quiet)
    marker.write_text("\n".join(done + [str(project)]), "utf-8")


def environment(folder: Path) -> ctypes.Array:
    """Our environment, with TEMP pointing somewhere the container can write."""
    temp = folder / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
    block = "".join(f"{k}={v}\0" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper()))
    return ctypes.create_unicode_buffer(block + "\0")


def kill_on_close_job() -> w.HANDLE:
    job = kernel32.CreateJobObjectW(None, None)
    _check(job)
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    _check(kernel32.SetInformationJobObject(
        job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)))
    return job


def run(project: Path, command: str) -> int:
    sid = container_sid()
    sid_str = sid_string(sid)
    folder = container_folder(sid_str)
    grant(project, sid_str, folder)

    caps = SECURITY_CAPABILITIES(AppContainerSid=sid)  # no capabilities: no network
    size = ctypes.c_size_t()
    kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    attrs = ctypes.create_string_buffer(size.value)
    _check(kernel32.InitializeProcThreadAttributeList(attrs, 1, 0, ctypes.byref(size)))
    try:
        _check(kernel32.UpdateProcThreadAttribute(
            attrs, 0, PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
            ctypes.byref(caps), ctypes.sizeof(caps), None, None))

        si = STARTUPINFOEXW()
        si.StartupInfo.cb = ctypes.sizeof(si)
        si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
        handles = [kernel32.GetStdHandle(n) for n in (-10, -11, -12)]
        for h in handles:  # the child can only receive handles marked inheritable
            if h:
                kernel32.SetHandleInformation(h, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT)
        si.StartupInfo.hStdInput, si.StartupInfo.hStdOutput, si.StartupInfo.hStdError = handles
        si.lpAttributeList = ctypes.cast(attrs, ctypes.c_void_p)

        shell = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        cmdline = ctypes.create_unicode_buffer(f'"{shell}" /d /s /c "{command}"')
        env = environment(folder)
        pi = PROCESS_INFORMATION()
        _check(kernel32.CreateProcessW(
            None, cmdline, None, None, True,
            EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT,
            env, None, ctypes.byref(si), ctypes.byref(pi)))
    finally:
        kernel32.DeleteProcThreadAttributeList(attrs)

    job = kill_on_close_job()  # closed when we exit, taking the command with it
    try:
        _check(kernel32.AssignProcessToJobObject(job, pi.hProcess))
        kernel32.ResumeThread(pi.hThread)
        kernel32.WaitForSingleObject(pi.hProcess, INFINITE)
        code = w.DWORD()
        _check(kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code)))
        return code.value
    finally:
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(pi.hProcess)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: win_sandbox.py <project dir> <command>")
    sys.exit(run(Path(sys.argv[1]).resolve(), sys.argv[2]))
