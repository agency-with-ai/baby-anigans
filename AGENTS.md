# Baby Anigans: running guide

Keep the agent small enough to trace by hand. The [README](README.md) explains the loop and saved examples; `agent.py --help` lists every option.

## Setup

Install [uv](https://docs.astral.sh/uv/) and, for local inference, [Ollama](https://ollama.com/download). uv uses the Python version in `.python-version`.

```sh
git clone https://github.com/agency-with-ai/baby-anigans.git
cd baby-anigans
uv venv && uv pip install -r requirements.txt
ollama pull qwen3:1.7b
uv run agent.py "What is the penalty for a late submission?" --trace first-run.jsonl
```

If Ollama is not running, start `OLLAMA_CONTEXT_LENGTH=8192 ollama serve` in another terminal. For hosted models, skip the Ollama commands and use Parley below.

Select your own UTF-8 file with `--file` and save the full conversation with `--trace`.

```sh
uv run agent.py "Your question" --file your-file.txt --trace baseline.jsonl
```

Trace files include retrieved text and cannot overwrite an existing file. Keep keys out of files and commits.

## Hosted models through Parley

Sign in to [Parley](https://platform.parley.mit.edu) with MIT Okta and copy your API key from **My Keys**. Set `PARLEY_API_KEY` in your shell, then run the same harness with a hosted model.

```sh
export PARLEY_API_KEY=your-parley-key
uv run agent.py "Are labs due in session?" --host https://parley.api.mit.edu/v1 --model claude-opus-5-5 --trace parley-claude.jsonl
```

To list available model IDs, run

```sh
curl -H "Authorization: Bearer $PARLEY_API_KEY" https://parley.api.mit.edu/v1/models
```

The harness runs locally; the question and retrieved text go to the provider through Parley. This calls the model directly, without Claude Code or another coding harness. See [Parley's documentation](https://parley-docs.mit.edu) for account and usage details.

## Experiments and traces

Run `uv run agent.py --help` for all flags.

- `--search-only` removes `read_lines` and its required-read check.
- `--note "Rule: answer entirely in capital letters."` adds an instruction after the question.
- `--compact 2` asks the LLM to summarize the history every two steps. Inspect the `compact` event and next request. `Evidence` retains its own record even when messages are dropped.
- `--stamp` puts the current time before the system prompt. Compare request prefixes and reported cache counts across runs.
- `--think` lets the model use its default reasoning effort; otherwise requests send `reasoning_effort: none`.

`[usage]` reports the server's prompt and cached token counts. Missing or translated counts cannot establish a cache effect. The default budget is eight loop steps; compaction adds extra model calls. `stop` distinguishes an accepted answer, empty-search abstention, step limit, and truncated output. A run without a completed answer exits with status 1.

## Testing a harness change

Keep the input, question, LLM, and settings fixed within each before-and-after comparison. For deadline questions, use `example/input.md`.

Choose one change and two tests, one showing its effect and one showing a remaining limitation. Predict both versions' results before editing.

- **Read limits.** Change `MAX_READ` or its tool description. Construct a call at the limit and inspect the returned lines or error.
- **Compaction.** Change `COMPACT_PROMPT`. Try “What should I do if I am sick?” with `--compact 2` and a capitalization note. First confirm the original run compacts; if it does not, try another question or area.
- **Answer checks.** Require citations to retrieved lines containing “except” or “however”. Test an answer missing the citation, then one that cites the line but gives the wrong deadline. Citation coverage cannot verify the explanation.

If the LLM never tries the relevant call, invoke Python directly. Save that output separately from LLM traces.

```python
from agent import FileTools, Evidence

files = FileTools("example/input.md")
evidence = Evidence(files)
for name, arguments in [
    ("search", {"query": "due in session"}),
    ("read_lines", {"start": 49, "end": 51}),
]:
    result, numbers = files.dispatch(name, arguments)
    print(result)
    if "error" not in result:
        evidence.record(name, arguments, numbers)
print(evidence.check("Labs are due in session. [L50]"))  # None means accepted.
```

Run the repo tests before and after editing. They use fake model responses and need no server.

```sh
uv run python -m unittest discover -s . -v
```

The saved-trace consistency test compares bundled examples with the original prompt and options. Changing those can cause an expected mismatch. Preserve the original traces and report that separately from behavioral failures.
