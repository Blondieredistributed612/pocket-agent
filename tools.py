"""
tools.py — Termux API wrappers exposed to the agent.

Every function here is callable by the model. Read this file before you trust
the agent with anything, especially `shell`.

Requires the Termux:API app (F-Droid) and `pkg install termux-api`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

# Absolute paths the agent is allowed to touch. Anything outside is refused.
ALLOWED_ROOTS = [Path.home()]

# Commands the shell tool will not run, regardless of what the model asks.
BLOCKED = ("rm -rf /", "mkfs", ":(){", "dd if=", "> /dev/")


def _run(cmd: list[str], timeout: int = 20) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr or "").strip() or "(no output)"
    except FileNotFoundError:
        return f"error: {cmd[0]} not found — is termux-api installed?"
    except subprocess.TimeoutExpired:
        return f"error: timed out after {timeout}s"


def _safe_path(path: str) -> Path | None:
    p = Path(path).expanduser().resolve()
    return p if any(root in p.parents or root == p for root in ALLOWED_ROOTS) else None


# ---------------------------------------------------------------------------
def notify(title: str, content: str = "") -> str:
    """Show an Android notification."""
    return _run(["termux-notification", "--title", title, "--content", content]) \
        and f"notification shown: {title}"


def speak(text: str) -> str:
    """Read text aloud through the device speaker."""
    _run(["termux-tts-speak", text], timeout=60)
    return f"spoken: {text[:60]}"


def read_file(path: str, max_chars: int = 4000) -> str:
    """Read a text file from the home directory."""
    p = _safe_path(path)
    if p is None:
        return "error: path outside allowed directory"
    if not p.is_file():
        return f"error: not a file: {p}"
    text = p.read_text(errors="replace")
    return text[:max_chars] + ("\n...(truncated)" if len(text) > max_chars else "")


def write_file(path: str, content: str) -> str:
    """Write a text file inside the home directory."""
    p = _safe_path(path)
    if p is None:
        return "error: path outside allowed directory"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"wrote {len(content)} chars to {p}"


def shell(command: str) -> str:
    """
    Run a shell command.

    DANGEROUS. A 4B model gets tool selection right roughly 70-80% of the time,
    which means it will occasionally run something you did not intend. The
    blocklist below is a speed bump, not a sandbox.
    """
    low = command.lower()
    if any(b in low for b in BLOCKED):
        return "refused: command matches blocklist"
    return _run(["sh", "-c", command], timeout=30)


def battery() -> str:
    """Battery level and charging state — useful for scheduling heavy work."""
    return _run(["termux-battery-status"])


# ---------------------------------------------------------------------------
REGISTRY = {
    "notify": notify,
    "speak": speak,
    "read_file": read_file,
    "write_file": write_file,
    "shell": shell,
    "battery": battery,
}

SCHEMA = [
    {"name": "notify", "description": "Show an Android notification.",
     "parameters": {"title": "string", "content": "string (optional)"}},
    {"name": "speak", "description": "Read text aloud.",
     "parameters": {"text": "string"}},
    {"name": "read_file", "description": "Read a text file under the home directory.",
     "parameters": {"path": "string"}},
    {"name": "write_file", "description": "Write a text file under the home directory.",
     "parameters": {"path": "string", "content": "string"}},
    {"name": "shell", "description": "Run a shell command and return its output.",
     "parameters": {"command": "string"}},
    {"name": "battery", "description": "Get battery level and charging state.",
     "parameters": {}},
]


def dispatch(name: str, args: dict) -> str:
    fn = REGISTRY.get(name)
    if fn is None:
        return f"error: unknown tool '{name}'. Available: {', '.join(REGISTRY)}"
    try:
        return str(fn(**args))
    except TypeError as e:
        return f"error: bad arguments for {name}: {e}"
    except Exception as e:
        return f"error: {name} failed: {e}"
