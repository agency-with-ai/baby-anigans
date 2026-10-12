# Baby Anigans

**Agent = LLM + harness.** Every agent is the same loop: an LLM asks for an action, a program performs it, the result goes back into the LLM's input, and the LLM is called again. Baby Anigans is that loop kept small enough that you can follow every turn and see how the internal mechanism works. It answers one question about one text file and must cite line numbers.

## The loop

The LLM (the *Model* lines below) is served by [Ollama](https://ollama.com). The harness is the Python around it: it runs the tools (*Tool* lines), checks answers (*Check* lines), and decides when to stop.

The bundled [`example/input.txt`](example/input.txt) is a short spec for a fictional feed-screening tool; every question in this README is about it. Below is a real run with a small local model, lightly trimmed. Every line not labeled *You* or *Model* was produced by Python.

```text
 1  You      What should happen if the feed is unavailable?

 2  Model    I could not find any evidence regarding what should happen...
    Check    Search the file before answering.

 3  Model    search(query="feed unavailable")
    Tool     25: If the feed is unavailable, report the failure and write no shortlist.

 4  Model    The evidence indicates that the system should report the failure...
    Check    Read neighboring lines too, not only the match. Call read_lines(24, 26).

 5  Model    read_lines(start=24, end=26)
    Tool     24: Failure behavior
             25: If the feed is unavailable, report the failure and write no shortlist.
             26: A failed run must not mark any entries read.

 6  Model    Line 24 mentions "Failure behavior", line 25 states...
    Check    Cite the retrieved evidence using [L25] or [L25-L26].

 7  Model    If the feed is unavailable, report the failure and write no shortlist. [L25]
    Check    Accepted.
```

What to notice:

- **Step 2.** The model's first move was to answer without looking. The harness refused and appended its refusal to the conversation, where the model reads it as if a user had typed it.
- **Step 3.** The model did not search anything. It asked for a search by name, and a Python function ran it. The line number comes from Python. The file was on disk the whole time, but the model saw line 25 only now, and lines 24 and 26 only at step 5.
- **Steps 4 and 6.** Two more answers bounced. Each bounce is a few lines of code you can read, and the budget of bounces is a number you can change.
- **Step 7.** The accepted answer cites a line the tools really returned. Nothing has checked that line 25 actually supports the claim. That is your job.

The trace file records every step, including the exact input the model received each time. The full trace of this run is [`example/feed-failure.jsonl`](example/feed-failure.jsonl). Each `request` row holds the complete message list sent to the model at that step, so the system prompt and every tool result repeat as the conversation grows. Open it to inspect a step, not to read top to bottom.

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

- Ask "Are all screened entries marked read?" The file has a rule on [line 29 and an exception on line 30](https://github.com/agency-with-ai/baby-anigans/blob/983e29ab571ada5b9bb41fc74e4a310aece913d8/example/input.txt#L29-L30). A search returns 29 alone. Did the model read 30? If the answer is wrong, was the exception missing from context, or present and ignored? One saved run: [`example/exception.jsonl`](example/exception.jsonl).
- Add `--search-only`. Same model, one tool fewer. Predict what breaks before you run it, then compare with [`example/exception-search-only.jsonl`](example/exception-search-only.jsonl), where every check passed and the answer is still wrong.
- Add `--model qwen3:8b`. Same harness, bigger model. Fewer corrections?
- Point `--file` at your own notes and ask something the file cannot answer. Does the agent say "I found nothing" or "there is nothing"?

## Setup

Python 3.10+ and [Ollama](https://ollama.com/download), then:

```sh
pip install -r requirements.txt
ollama pull qwen3:1.7b
python agent.py "What should happen if the feed is unavailable?" --trace first-run.jsonl
```

Flags, model sizes, limits, stop reasons, and tests are in [docs/running-baby-anigans.md](docs/running-baby-anigans.md).

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. [Project spec](docs/baby-anigans-project-spec.md). [Tests](test_agent.py) run against a fake model, no Ollama needed. [MIT license](LICENSE).
