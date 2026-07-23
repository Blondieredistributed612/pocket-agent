"""System prompt and tool-call format for a 4B model."""

import json

from tools import SCHEMA


def _fmt(schema):
    lines = []
    for t in schema:
        params = ", ".join(f"{k}: {v}" for k, v in t["parameters"].items()) or "none"
        lines.append(f"- {t['name']}({params}) — {t['description']}")
    return "\n".join(lines)


SYSTEM = f"""You are a personal assistant running locally on an Android device.

Available tools:
{_fmt(SCHEMA)}

To use a tool, reply with ONLY this JSON and nothing else:

{{"tool": "<name>", "args": {{...}}}}

To answer directly, reply with plain text and no JSON.

Rules:
- One tool per reply. Wait for the result before the next step.
- After a tool returns, either use another tool or give a short final answer.
- Never invent tool output. If a tool errors, say so.
- Keep replies short. You are running on a tablet.
"""

# Small models drift after a few turns. Re-stating the format helps.
REMINDER = ('Reply with either one JSON tool call {"tool": ..., "args": {...}} '
            "or a plain-text answer.")

MAX_STEPS = 6   # hard stop; 4B models will loop given the chance
