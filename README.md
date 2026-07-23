# pocket-agent

A tool-calling LLM agent designed to run entirely on an Android device via
Termux and llama.cpp. No cloud, no API key, nothing leaving the device.

> **Status: early stage.** The install path and the agent loop are here; the
> tablet deployment is not yet something I run daily. See
> [Known constraints](#known-constraints) for what you should expect on tablet
> hardware, and [Roadmap](#roadmap) for where it is going.
>
> No throughput figures are published yet — I would rather leave that blank
> than guess at it.

---

## Why this exists

Every "run an LLM locally" guide assumes a desktop with a discrete GPU. Modern
ARM tablets have enough memory to hold a 4B model, so the question is whether
the rest of the path is practical.

Three things cost the most time on the way there:

1. **The Play Store Termux is abandoned** and its API bridge is broken. Most
   failed setups die here.
2. **`GGML_CPU_KLEIDIAI` is off by default** and it is the flag that matters on
   ARM.
3. **A 4B model needs a different agent loop** than a frontier model. Chained
   tool calls do not work; one call per turn does.

The third point is the part that generalises. The loop in this repo is built
around what small models actually fail at, and it works the same whether the
server runs on a tablet, a laptop, or a Raspberry Pi.

---

## What the agent does

```
You            "remind me in 20 minutes to check the training run"
Agent          → termux-notification
               → confirms

You            "what's in ~/experiments/results.json"
Agent          → reads the file
               → summarises it

You            "say that out loud"
Agent          → termux-tts-speak
```

Six tools: notification, text-to-speech, file read, file write, shell, battery.
The loop is ~150 lines and easy to extend.

---

## Hardware notes

| Role | Device | Reasoning |
|---|---|---|
| Brain | Galaxy Tab S10 FE+ — Exynos 1580, 8 GB | enough headroom for a 4B model at Q4 |
| Thin client | Galaxy A34 — Dimensity 1080, 6 GB | too tight for 4B locally; connects over Wi-Fi instead |

Roughly: 8 GB RAM and a recent ARM SoC for a 4B model at Q4. On 6 GB devices,
drop to a 1.5B model or use the thin-client setup below.

**No throughput numbers published yet.** Benchmarking is on the roadmap; until
then a guess would make the rest of this document less trustworthy. If you
measure it on your device, please open an issue:

```bash
llama-bench -m ~/models/Qwen3-4B-Instruct-Q4_K_M.gguf
```

---

## Setup

This is the path I followed. Expect to adapt it — Termux, llama.cpp and the model repos all move quickly. If a step is stale, an issue or PR is welcome.

### 1. Termux — from F-Droid, not Play Store

```
https://f-droid.org/packages/com.termux/
https://f-droid.org/packages/com.termux.api/
```

The Play Store build is abandoned and its API bridge no longer works. Install
**both** Termux and Termux:API. This is the single most common failure point.

### 2. Dependencies

```bash
pkg update && pkg upgrade
pkg install python clang cmake git termux-api
pip install httpx
```

### 3. Build llama.cpp with the ARM flag

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CPU_KLEIDIAI=ON
cmake --build build --config Release -j $(nproc)
```

`GGML_CPU_KLEIDIAI=ON` enables ARM's KleidiAI kernels. It is **not** on by
default and it is the difference between usable and painful on these chips.

### 4. Model

```bash
mkdir -p ~/models && cd ~/models
# Qwen3-4B-Instruct-Q4_K_M.gguf from Hugging Face
```

Q4_K_M is the sensible trade-off: ~2.5 GB, leaves room for Android's own memory
pressure, and quality loss versus Q8 is small for tool calling.

### 5. Start the server

```bash
termux-wake-lock          # survive screen-off
~/llama.cpp/build/bin/llama-server \
  -m ~/models/Qwen3-4B-Instruct-Q4_K_M.gguf \
  --port 8080 \
  --ctx-size 4096
```

### 6. Run the agent

```bash
python agent.py
```

---

## Thin client over Wi-Fi

Bind to the network instead of loopback:

```bash
llama-server -m model.gguf --host 0.0.0.0 --port 8080
```

From the second device:

```bash
python agent.py --server http://<tablet-ip>:8080
```

One brain, two devices. The tablet does the work.

> Trusted networks only. The llama.cpp server has no authentication.

---

## Designing an agent loop for a 4B model

This is the part that generalises beyond Android. Small models fail in specific,
predictable ways, and the loop compensates for each:

| Failure | Compensation |
|---|---|
| Chained tool calls in one reply | one call per turn, wait for the result |
| Infinite loops | hard step cap (`MAX_STEPS = 6`) |
| Format drift after ~3 turns | re-inject the format reminder every turn |
| Malformed JSON | feed the parse error back instead of crashing |
| Invented tool output | explicit instruction never to fabricate results |

Expect roughly **70-80% accuracy on tool selection** for a 4B model — a widely
reported range, not something I measured here. That is fine for a personal
assistant with a human watching, and not fine for anything unattended.

### Hybrid fallback

Realistic design is local-first with an escape hatch:

```
request → complexity heuristic
            ├─ simple  → local model
            └─ complex → remote API
```

Offline it degrades instead of dying. `--fallback` enables it.

---

## Verify the loop without a model

The agent loop, the tool-call parser and the safety guards can be checked on any
machine — no Android, no llama.cpp, no download:

```bash
python test_agent.py
```

It runs the loop against a scripted fake backend and checks that a plain answer
terminates, a tool call executes, the step cap stops a looping model, the shell
blocklist holds, and paths outside the home directory are refused.

A model server is only needed for real inference.

## Repository contents

```
agent.py        loop, tool-call parsing, optional remote fallback
tools.py        Termux API wrappers — notification, TTS, files, shell, battery
prompts.py      system prompt and tool schema
test_agent.py   offline checks — no model or device required
```

---

## Roadmap

- [ ] Benchmark and publish real throughput figures
- [ ] Telegram front-end via long polling — no static IP, works off Wi-Fi,
      and sidesteps the on-device storage cost entirely
- [ ] Battery-aware scheduling — defer heavy calls when unplugged
- [ ] RAG over local notes — `sqlite-vec` + `all-MiniLM` ONNX, both CPU-cheap
- [ ] Smaller-model path (1.5B) for 6 GB devices
- [ ] Voice input via `termux-speech-to-text`

Issues and PRs welcome, particularly benchmark numbers from other devices.

---

## Known constraints

Tablet hardware imposes real limits. Worth knowing before you start, because
most guides skip them:

**Storage.** The GGUF file, llama.cpp's build tree and the Termux environment
add up to several gigabytes. On a device also holding photos and apps, that is
not space you forget about.

**Thermals and responsiveness.** Phones and tablets have no active cooling. With
the server resident, the device gets warm and general responsiveness drops. The
same model that is comfortable on a laptop makes a tablet feel sluggish.

**The network hop is usually worth it.** If full offline operation is not a hard
requirement, running the server on a machine you already own and connecting from
the tablet costs nothing in storage or heat, and lets you use a larger model.
`--server` already supports this, and for most use cases it is the better
default. Fully-on-device is the interesting case, not the practical one — at
least at 4B on current tablet silicon.

None of this is a llama.cpp or Qwen problem. It is what a 4B model costs on
hardware built for a different job, and it will keep improving as both the
runtimes and the chips do.

## Security

- The shell tool runs arbitrary commands. There is a blocklist and a home-directory
  restriction, but that is a speed bump, not a sandbox. **Read `tools.py`.**
- `--host 0.0.0.0` exposes an unauthenticated LLM server to your local network.
- Nothing leaves the device unless you pass `--fallback`.

---

## License

MIT
