# Baby Anigans

**Agent = LLM + harness.** Baby Anigans answers one question about one text file. The LLM requests tools and proposes answers. Python runs the tools, checks answers, and decides whether to continue.

Point your agents to [running guide](AGENTS.md) for setting up the repo.

## Example run

This is a trimmed example run, on the bundled [course policy](example/input.md). Every line except *You* and *Model* comes from Python.

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

- The model initially answers without looking. Python rejects it and adds feedback to the next request.
- The model requests `search`; Python reads the file and returns numbered lines. The model sees only the returned text.
- Python requires a neighboring-line read, even though the answer already cites a real line. Here those neighbors are blank.
- The answer passes, but line 127's automatic extensions never reached the model. Valid citations do not guarantee a complete answer.

Open the [full trace](example/late-penalty.jsonl) at a `request` event to see exactly what the model received. Each request repeats the conversation so far. `tool` events record Python results; `check` events record rejected answers; `stop` records why the loop ended.

## Read the code

[agent.py](agent.py) contains the whole agent, about 300 lines.

| Name | Role |
|---|---|
| `SYSTEM` | Instructions the LLM reads |
| `TOOLS` | Descriptions and argument schemas for `search` and `read_lines` |
| `FileTools` | Python functions that search and read the selected file |
| `Evidence` | Records returned lines and checks proposed answers |
| `run_agent` | Calls the LLM, dispatches tools, checks, and continues or stops |
| `COMPACT_PROMPT` | Instructions for summarizing history when `--compact` is enabled |

Compare `SYSTEM` with `Evidence.check`. The prompt asks for complete, supported answers. Python checks only that searches ran, a match's neighbors were read, and citations refer to returned lines. If all searches are empty, Python supplies a fixed abstention after two distinct queries. Neither acceptance nor abstention proves what the file says.

The operator chooses the file. The model cannot change paths, run a shell, or write files through these tools.

## Inspect the saved examples

Recorded October 12, 2026, at temperature 0 with thinking off. The local runs use `qwen3:1.7b` on Ollama 0.35.1; the hosted runs use the same Python harness through Parley. These are individual runs, not a model ranking.

| Trace in `example/` | What to inspect |
|---|---|
| [late-penalty.jsonl](example/late-penalty.jsonl) | The automatic extensions never reached the LLM. |
| [lab-deadline.jsonl](example/lab-deadline.jsonl) | The deadline auto extension reached the LLM but disappeared from the answer. |
| [lab-deadline-search-only.jsonl](example/lab-deadline-search-only.jsonl) | One fewer tool with `--search-only`. What evidence still arrived? |
| [sick.jsonl](example/sick.jsonl) | Two relevant passages were retrieved. Which did the answer use? |
| [lab-deadline-claude-opus-5-5.jsonl](example/lab-deadline-claude-opus-5-5.jsonl) | A hosted Claude run that kept the deadline auto extension. |
| [lab-deadline-gpt-5.6-sol.jsonl](example/lab-deadline-gpt-5.6-sol.jsonl) | A hosted GPT run that kept it, using its own searches and read window. |

Try your own file and question, or change one part of the harness using the [testing guide](AGENTS.md#testing-a-harness-change).

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. [MIT license](LICENSE).
