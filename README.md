# Baby Anigans

An agent small enough to understand completely. One Python file, two tools, no framework.

## Why this exists

You will spend years working alongside agents: coding assistants, research tools, things that book travel and triage inboxes. All of them are the same loop. A model asks for an action, a program performs it, the result is pasted into the model's input, and the model is called again. That loop decides what the agent can see, what it can do, and what stops it. Products hide it. Frameworks abstract it. Most people who use agents every day have never watched one turn of it.

Baby Anigans is that loop with nothing hidden. After an afternoon with it you should be able to answer, about any agent you meet:

- What can it actually see right now, as opposed to what exists on disk or on the web?
- When it "searched", who searched, and what did the search really do?
- When it corrects itself, was that the model's idea or a rule somebody wrote in Python?
- What is checked before the answer reaches you, and what is not checked at all?

Those questions are the difference between using an agent and being used by one.

## What one run looks like

Three words are used throughout. The **agent** is the whole program, Baby Anigans. The **model** is the language model inside it, served by Ollama. The **harness** is the Python around the model: it runs the tools, checks answers, and decides when to stop.

The agent answers one question about one text file and must cite line numbers. Below is a real run with a small local model, lightly trimmed. Every line not labeled *Model* was produced by Python.

```text
 1  You      What should happen if the feed is unavailable?

 2  Model    I could not find any evidence regarding what should happen...
    Harness  Search the file before answering.

 3  Model    search(query="feed unavailable")
    Tool     25: If the feed is unavailable, report the failure and write no shortlist.

 4  Model    The evidence indicates that the system should report the failure...
    Harness  Read neighboring lines too, not only the match. Call read_lines(24, 26).

 5  Model    read_lines(start=24, end=26)
    Tool     24: Failure behavior
             25: If the feed is unavailable, report the failure and write no shortlist.
             26: A failed run must not mark any entries read.

 6  Model    Line 24 mentions "Failure behavior", line 25 states...
    Harness  Cite the retrieved evidence using [L25] or [L25-L26].

 7  Model    If the feed is unavailable, report the failure and write no shortlist. [L25]
    Harness  Accepted.
```

What to notice:

- **Step 2.** The model's first move was to answer without looking. The harness refused and appended its refusal to the conversation, where the model reads it as if a user had typed it.
- **Step 3.** The model did not search anything. It asked for a search by name, and a Python function ran it. The line number comes from Python.
- **Steps 4 and 6.** Two more answers bounced. Each bounce is a few lines of code you can read, and the budget of bounces is a number you can change.
- **Step 7.** The accepted answer cites a line the tools really returned. Nothing has checked that line 25 actually supports the claim. That is your job.

The file was on disk the whole time. The model saw line 25 only after step 3, and lines 24 and 26 only after step 5. The full record of every step, including the exact input the model received each time, is in the trace file.

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
