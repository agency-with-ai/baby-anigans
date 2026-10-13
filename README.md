# Baby Anigans

**Agent = LLM + harness.** Every agent is the same loop: an LLM asks for an action, a program performs it, the result goes back into the LLM's input, and the LLM is called again. Baby Anigans is that loop kept small enough that you can follow every turn and see how the internal mechanism works. It answers one question about one text file and must cite line numbers.

## The loop

The LLM (the *Model* lines below) is served by [Ollama](https://ollama.com). The harness is the Python around it: it runs the tools (*Tool* lines), checks answers (*Check* lines), and decides when to stop.

The bundled [`example/input.md`](example/input.md) is the 6.390 course information and grading page, copied from the course website; every question in this README is about it. Below is a real run with a small local model, lightly trimmed. Every line not labeled *You* or *Model* was produced by Python.

```text
 1  You      What is the penalty for a late submission?

 2  Model    I cannot determine the penalty for a late submission as the file was not provided.
    Check    Search the file before answering.

 3  Model    search(query="penalty late submission")
    Tool     125: Late submissions incur a 20% penalty per day, applied linearly (so 1 hour late is -0.83%). See the extension policy below.

 4  Model    The penalty for a late submission is 20% per day, applied linearly. [L125]
    Check    Read neighboring lines too, not only the match. Call read_lines(124, 126).

 5  Model    read_lines(start=124, end=126)
    Tool     124:
             125: Late submissions incur a 20% penalty per day, applied linearly (so 1 hour late is -0.83%). See the extension policy below.
             126:

 6  Model    The penalty for a late submission is 20% per day, applied linearly. [L125]
    Check    Accepted.
```

What to notice:

- **Step 2.** The model's first move was to answer without looking. It even said the file was not provided, which is true: the model never gets the file, only tool results. The harness refused and appended its refusal to the conversation, where the model reads it as if a user had typed it.
- **Step 3.** The model did not search anything. It asked for a search by name, and a Python function ran it. The line number comes from Python. The file was on disk the whole time, but the model saw line 125 only now, and lines 124 and 126 only at step 5.
- **Step 4.** A correct answer bounced anyway, because a rule says read around the match first. The rule is a few lines of code you can read, and the budget of bounces is a number you can change. Here the neighbors were blank lines, so the rule bought nothing. On another question it is the difference between the rule and its exception.
- **Step 6.** The accepted answer cites a line the tools really returned. Nothing has checked that line 125 actually supports the claim, or that "see the extension policy below" does not change it. That is your job.

The trace file records every step, including the exact input the model received each time. The full trace of this run is [`example/late-penalty.jsonl`](example/late-penalty.jsonl). Each `request` row holds the complete message list sent to the model at that step, so the system prompt and every tool result repeat as the conversation grows. The requests are in the OpenAI chat format that Ollama and most hosted providers accept, which is why one `--host` flag can point the same harness at a different model. Open it to inspect a step, not to read top to bottom.

## Where the pieces are

[agent.py](agent.py) is about 300 lines.

| Name in the code | What it is |
|---|---|
| `TOOLS` | The JSON schema the model sees: two functions, `search` and `read_lines` |
| `FileTools` | The Python that actually runs when the model asks for those |
| `Evidence` | What the harness knows the model has seen, and the checks it applies to an answer |
| `run_agent` | The loop: call the model, run tools, check, continue or stop |
| `SYSTEM` | The instructions. Compare with `Evidence.check`: one asks, the other enforces |
| `COMPACT_PROMPT` | What the harness asks the model to keep when `--compact` throws the history away |

The checks are narrow on purpose. Python can verify that the model searched, read around the match, and cited lines the tools returned. Python cannot verify that line 125 supports the claim. Seeing exactly where that boundary sits is most of the lesson, and it is the same boundary in every agent you will ever use.

## Things to try

Each takes a minute and the trace shows what changed.

- Ask "Are labs due in session?" The rule and its exception share [line 50](https://github.com/agency-with-ai/baby-anigans/blob/480c3e00c2816838e9f6249a49dc473e4c95a9aa/example/input.md#L50): due in session, unless the first checkoff is done. A search returns that whole line, so the exception is in context. Did the answer mention it? In [`example/lab-deadline.jsonl`](example/lab-deadline.jsonl) it did not.
- Add `--search-only`. Same model, one tool fewer. Predict what breaks before you run it, then compare with [`example/lab-deadline-search-only.jsonl`](example/lab-deadline-search-only.jsonl).
- Ask "What should I do if I am sick?" The file answers twice, on the info page and in more detail on the grading page. In [`example/sick.jsonl`](example/sick.jsonl) the search found both and the model read around one. Was the second answer missing from context, or present and ignored?
- Add `--model qwen3:8b`. Same harness, bigger model. Fewer corrections? In our run it still answered "Yes, labs are due in session" without the exception. Pointing `--host` at a hosted provider changes nothing else: [`example/lab-deadline-claude-opus-5-5.jsonl`](example/lab-deadline-claude-opus-5-5.jsonl) and [`example/lab-deadline-gpt-5.6-sol.jsonl`](example/lab-deadline-gpt-5.6-sol.jsonl) are the same question through the same harness, and both read a window of lines unprompted and stated the exception first. Compare where in the three traces the exception was in context, and when it was used.
- Watch the `[usage]` line. Every step resends the whole conversation, and the server reports how much of it was served from its prefix cache. Add `--stamp`, which puts the current time at the top of the system prompt, and run twice: the first step's cache count drops to a handful of tokens, because the prefix now differs between runs. What does that say about where to put volatile text?
- Add `--compact 2 --note "Rule: write your final answer entirely in capital letters."` and ask about being sick. Every two steps the harness replaces the history with a model-written summary and records what it dropped. Did the rule survive compaction? Read `COMPACT_PROMPT` in `agent.py`, remove the clause about instructions, and run again. Then put the rule in the system prompt instead. Whatever survives is whatever the harness chose to carry.
- Point `--file` at your own notes and ask something the file cannot answer. Does the agent say "I found nothing" or "there is nothing"?

## Setup

Python 3.10+ and [Ollama](https://ollama.com/download), then:

```sh
pip install -r requirements.txt
ollama pull qwen3:1.7b
python agent.py "What is the penalty for a late submission?" --trace first-run.jsonl
```

Flags, model sizes, limits, stop reasons, and tests are in [docs/running-baby-anigans.md](docs/running-baby-anigans.md).

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. [Project spec](docs/baby-anigans-project-spec.md). [Tests](test_agent.py) run against a fake model, no server needed. [MIT license](LICENSE).
