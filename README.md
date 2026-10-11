# Baby Anigans

An agent small enough to understand completely. One Python file, two tools, no framework.

## Why this exists

You will spend years working alongside agents: coding assistants, research tools, things that book travel and triage inboxes. All of them are the same loop. A model asks for an action, a program performs it, the result is pasted into the model's input, and the model is called again. That loop decides what the agent can see, what it can do, and what stops it. Products hide it. Frameworks abstract it. Most people who use agents every day have never watched one turn of it.

Baby Anigans is one turn of that loop, repeated, with nothing hidden. After an afternoon with it you should be able to answer, about any agent you meet:

- What can it actually see right now, as opposed to what exists on disk or on the web?
- When it "searched", who searched, and what did the search really do?
- When it corrects itself, was that the model's idea or a rule somebody wrote in Python?
- What is checked before the answer reaches you, and what is not checked at all?

Those questions are the difference between using an agent and being used by one.

## What it looks like

The agent answers one question about one text file and must cite line numbers. Here is a real run with a small local model, trimmed. Lines marked `tool` and `check` were written by Python, not the model.

```text
user       What should happen if the feed is unavailable?
assistant  I could not find any evidence regarding what should happen...
check      Search the file before answering.
assistant  → search {"query": "feed unavailable"}
tool       25: If the feed is unavailable, report the failure and write no shortlist.
assistant  The evidence indicates that if the feed is unavailable, the system should report...
check      Read neighboring lines too, not only the match. Call read_lines(start=24, end=26).
assistant  → read_lines {"start": 24, "end": 26}
tool       24: Failure behavior
           25: If the feed is unavailable, report the failure and write no shortlist.
           26: A failed run must not mark any entries read.
assistant  The lines retrieved show that line 24 mentions "Failure behavior", line 25...
check      Cite the retrieved evidence using [L25] or [L25-L26].
assistant  If the feed is unavailable, report the failure and write no shortlist. [L25]
```

Read it top to bottom. The model's first move was to answer from nothing. Three times a proposed answer was bounced back by a rule in Python, and each bounce was appended to the conversation as if a user had typed it. The file was on disk the whole time, but the model saw line 25 only after a tool returned it. Every one of those facts is visible in the saved trace, and every rule that produced a `check` line is a few lines of code you can read and change.

## Where the pieces are

[agent.py](agent.py) is about 250 lines.

| Name in the code | What it is |
|---|---|
| `TOOLS` | The JSON schema the model sees: two functions, `search` and `read_lines` |
| `FileTools` | The Python that actually runs when the model asks for those |
| `Evidence` | What the harness knows the model has seen, and the checks it applies to an answer |
| `run_agent` | The loop: call the model, run tools, check, continue or stop |
| `SYSTEM` | The instructions. Compare with `Evidence.check`: one asks, the other enforces |

The checks are narrow on purpose. Python can verify that the model searched, read around the match, and cited lines the tools returned. Python cannot verify that line 25 supports the claim. Seeing exactly where that boundary sits is most of the lesson, and it is the same boundary in every agent you will ever use.

## Things to try

Each takes a minute and the trace shows what changed.

- Ask "Are all screened entries marked read?" The file has a rule on line 29 and an exception on line 30. A search returns 29 alone. Did the model read 30? If the answer is wrong, was the exception missing from context, or present and ignored?
- Add `--search-only`. Same model, one tool fewer. Predict what breaks before you run it.
- Add `--model qwen3:8b`. Same harness, bigger model. Fewer corrections?
- Point `--file` at your own notes and ask something the file cannot answer. Does the agent say "I found nothing" or "there is nothing"?

## Setup

Everything needed to install and run is in [docs/reference.md](docs/reference.md), written so a person or a coding agent can follow it without further context. Short version: Python 3.10+, [Ollama](https://ollama.com/download), `pip install -r requirements.txt`, `ollama pull qwen3:1.7b`, then

```sh
python agent.py "What should happen if the feed is unavailable?" --trace first-run.jsonl
```

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. [Project spec](project-spec.md). [Tests](test_agent.py) run against a fake model, no Ollama needed. [MIT license](LICENSE).
