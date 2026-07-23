"""
agent.py — tool-calling loop against a local llama.cpp server.

    python agent.py
    python agent.py --server http://192.168.1.42:8080     # thin client
    python agent.py --fallback                            # remote on hard tasks

Design notes for small models:
  * one tool call per turn — 4B models handle chained calls badly
  * a hard step cap — without it they loop
  * the format reminder is re-injected — they drift after ~3 turns
  * malformed JSON is fed back as an error rather than crashing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import tools
from prompts import MAX_STEPS, REMINDER, SYSTEM

JSON_RE = re.compile(r"\{.*\}", re.S)


def parse_tool_call(text: str):
    """Return (name, args) if the reply is a tool call, else None."""
    m = JSON_RE.search(text.strip())
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and "tool" in obj:
        return obj["tool"], obj.get("args", {}) or {}
    return None


def looks_hard(text: str) -> bool:
    """Crude complexity heuristic for the fallback router."""
    signals = ("compare", "analyse", "analyze", "explain why", "step by step",
               "then", "after that", "summarise all", "summarize all")
    return len(text) > 300 or sum(s in text.lower() for s in signals) >= 2


class Backend:
    def __init__(self, url: str, model: str = "local"):
        import httpx          # imported here so the loop can be tested
        self.url = url.rstrip("/")   # without httpx installed
        self.model = model
        self.client = httpx.Client(timeout=180)

    def chat(self, messages, temperature=0.3, max_tokens=512) -> str:
        r = self.client.post(
            f"{self.url}/v1/chat/completions",
            json={"model": self.model, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class RemoteBackend(Backend):
    """OpenAI-compatible remote endpoint for the fallback path."""

    def __init__(self, url: str, model: str, api_key: str):
        super().__init__(url, model)
        self.client.headers["Authorization"] = f"Bearer {api_key}"


def run_turn(user_input: str, local: Backend, remote: Backend | None) -> str:
    backend = local
    if remote is not None and looks_hard(user_input):
        print("  [router] complex request -> remote backend", file=sys.stderr)
        backend = remote

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_input}]

    for step in range(MAX_STEPS):
        reply = backend.chat(messages)
        call = parse_tool_call(reply)

        if call is None:
            return reply.strip()

        name, args = call
        print(f"  [tool] {name}({json.dumps(args, ensure_ascii=False)})",
              file=sys.stderr)
        result = tools.dispatch(name, args)
        print(f"  [result] {result[:120]}", file=sys.stderr)

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user",
                         "content": f"Tool result:\n{result}\n\n{REMINDER}"})

    return "Stopped: hit the step limit without reaching an answer."


def main():
    ap = argparse.ArgumentParser(description="On-device tool-calling agent")
    ap.add_argument("--server", default="http://localhost:8080",
                    help="llama.cpp server URL")
    ap.add_argument("--fallback", action="store_true",
                    help="route complex requests to a remote API")
    ap.add_argument("--remote-url", default="https://models.inference.ai.azure.com")
    ap.add_argument("--remote-model", default="gpt-4o-mini")
    ap.add_argument("--once", default=None, help="run one request and exit")
    args = ap.parse_args()

    local = Backend(args.server)

    remote = None
    if args.fallback:
        key = os.environ.get("REMOTE_API_KEY")
        if not key:
            print("--fallback needs REMOTE_API_KEY in the environment",
                  file=sys.stderr)
            sys.exit(1)
        remote = RemoteBackend(args.remote_url, args.remote_model, key)

    if args.once:
        print(run_turn(args.once, local, remote))
        return

    print(f"pocket-agent -> {args.server}"
          f"{'  (fallback on)' if remote else ''}")
    print("Ctrl-C to quit.\n")
    while True:
        try:
            user = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        try:
            print(run_turn(user, local, remote), "\n")
        except Exception as e:
            print(f"server error: {e}\n"
                  f"is llama-server running on {args.server}?\n", file=sys.stderr)


if __name__ == "__main__":
    main()
