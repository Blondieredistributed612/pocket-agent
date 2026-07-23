"""
test_agent.py — verify the agent loop without a model, a server, or Android.

    python test_agent.py

Uses a scripted fake backend, so the loop, the tool-call parser and the safety
guards can be checked on any machine. Nothing is downloaded and nothing is
installed.
"""

from __future__ import annotations

import json
import sys

import tools
from agent import parse_tool_call, looks_hard
from prompts import MAX_STEPS


# ---------------------------------------------------------------------------
class FakeBackend:
    """Returns a scripted sequence of replies instead of calling a model."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, **kw):
        self.calls += 1
        return self.replies.pop(0) if self.replies else "Done."


def run_turn_fake(user_input, backend):
    """Same control flow as agent.run_turn, without the network."""
    messages = [{"role": "user", "content": user_input}]
    trace = []
    for _ in range(MAX_STEPS):
        reply = backend.chat(messages)
        call = parse_tool_call(reply)
        if call is None:
            return reply.strip(), trace
        name, args = call
        result = tools.dispatch(name, args)
        trace.append((name, args, result))
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})
    return "Stopped: hit the step limit.", trace


# ---------------------------------------------------------------------------
def check(label, condition, detail=""):
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {label}" + (f"  — {detail}" if detail and not condition else ""))
    return condition


def main():
    ok = True
    print("\n1. Tool-call parser")
    cases = [
        ('{"tool": "battery", "args": {}}', ("battery", {})),
        ('Sure! {"tool": "speak", "args": {"text": "hi"}}', ("speak", {"text": "hi"})),
        ("Just a plain answer.", None),
        ("{broken json", None),
        ('{"result": 5}', None),
    ]
    for text, expected in cases:
        got = parse_tool_call(text)
        ok &= check(f"{text[:38]!r:<42} -> {got}", got == expected, f"expected {expected}")

    print("\n2. Safety guards")
    ok &= check("shell blocklist",
                "refused" in tools.dispatch("shell", {"command": "rm -rf /"}))
    ok &= check("unknown tool rejected",
                "unknown tool" in tools.dispatch("nope", {}))
    ok &= check("path outside home rejected",
                "outside allowed" in tools.dispatch("read_file", {"path": "/etc/passwd"}))
    ok &= check("bad arguments handled",
                "bad arguments" in tools.dispatch("notify", {"wrong": 1}))

    print("\n3. File tools round-trip")
    import tempfile, os
    from pathlib import Path
    tmp = Path.home() / ".pocket_agent_test.txt"
    tools.dispatch("write_file", {"path": str(tmp), "content": "hello agent"})
    back = tools.dispatch("read_file", {"path": str(tmp)})
    ok &= check("write then read", back.strip() == "hello agent", f"got {back!r}")
    tmp.unlink(missing_ok=True)

    print("\n4. Loop terminates on a plain answer")
    b = FakeBackend(["The battery is fine."])
    answer, trace = run_turn_fake("how's the battery", b)
    ok &= check("no tool called", len(trace) == 0)
    ok &= check("answer returned", answer == "The battery is fine.")

    print("\n5. Loop executes a tool then answers")
    b = FakeBackend([
        '{"tool": "write_file", "args": {"path": "~/.pa_demo.txt", "content": "x"}}',
        "Wrote the file.",
    ])
    answer, trace = run_turn_fake("write a file", b)
    ok &= check("one tool call recorded", len(trace) == 1, f"got {len(trace)}")
    ok &= check("final answer returned", answer == "Wrote the file.")
    (Path.home() / ".pa_demo.txt").unlink(missing_ok=True)

    print("\n6. Step cap stops a looping model")
    b = FakeBackend(['{"tool": "battery", "args": {}}'] * 50)
    answer, trace = run_turn_fake("loop forever", b)
    ok &= check(f"capped at {MAX_STEPS} steps", len(trace) == MAX_STEPS, f"got {len(trace)}")
    ok &= check("reports the cap", "step limit" in answer)

    print("\n7. Fallback heuristic")
    ok &= check("simple request stays local", not looks_hard("what's the battery"))
    ok &= check("complex request routes out",
                looks_hard("read the file then compare it step by step with the other one"))

    print()
    if ok:
        print("All checks passed. The loop, parser and guards work on this machine.")
        print("A model server is only needed for real inference.")
    else:
        print("Some checks failed — see above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
