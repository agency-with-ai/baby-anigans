# Baby Anigans: running guide

Setup, models, flags, limits, saved traces, and tests, written so that a person or a coding agent working in this repository can follow it without further context. The [README](README.md) walks through one run of the loop; the [project spec](project-spec.md) says what the agent is for.

## Setup

Choose local Ollama or hosted models through Parley. Both paths use [uv](https://docs.astral.sh/uv/) and the Python client. For local inference, also install [Ollama](https://ollama.com/download). The repository pins Python 3.12 in `.python-version`, and uv fetches it if the machine lacks it. The commands below set up local inference. No Ollama account is needed, and after the model download everything runs offline. For Parley, clone the repository and install the Python dependencies with the first three commands, then skip the Ollama commands and follow [Hosted models through Parley](#hosted-models-through-parley).

```sh
git clone git@github.com:agency-with-ai/baby-anigans.git
cd baby-anigans
uv venv && uv pip install -r requirements.txt
ollama pull qwen3:1.7b
uv run agent.py "What is the penalty for a late submission?" --trace first-run.jsonl
```

If Ollama is not already running, start `ollama serve` in another terminal. The agent talks to Ollama through its OpenAI-compatible endpoint, `http://localhost:11434/v1`, using the `openai` Python package from `requirements.txt`. `uv run` uses the `.venv` that `uv venv` made, so no activation step is needed; activate it if you prefer to type `python` directly. The same client reaches any server that speaks that protocol, so one `--host` flag covers local Ollama and hosted providers. Ollama's compatibility endpoint does not take a context length per request; if the default is below 8K on your machine, start the server with `OLLAMA_CONTEXT_LENGTH=8192 ollama serve`.

## Models

| Model | Download | Memory when loaded |
|---|---|---|
| `qwen3:1.7b` (default) | 1.4 GB | 2.4 GB |
| `qwen3:8b` | 5.2 GB | 6.6 GB |

Memory is what Ollama reported on our M4 Max Studio at the configured 8K context; allow extra for the OS and other applications. We have not measured student laptops. A 16 GB laptop is a planning target for the larger model, not a tested minimum.

The default is a toy for inspecting the loop. It can choose poor search queries, miss evidence, or fail the citation checks, and completing one question says nothing about the next. `--model qwen3:8b` answered the late-penalty question with a citation and abstained on a question the file cannot answer in local smoke runs, but it still answered "Yes, labs are due in session" and dropped the exception; a bigger model is not a correctness guarantee.

## Hosted models through Parley

[Parley](https://parley-docs.mit.edu) is MIT's gateway to commercial models, and every MIT student has an account. Getting a key takes a minute:

1. Sign in at [platform.parley.mit.edu](https://platform.parley.mit.edu) with your MIT Okta login. The account is created on first login with $10 of free credit, replenished on the 1st of each month.
2. Open **My Keys** in the sidebar and click the eye icon to reveal your `sk-parley-v1-...` key. Copy it somewhere safe and never commit it.

With the key and Python dependencies installed, the same agent runs Claude, GPT, or Gemini models without Ollama or a local model:

```sh
export OPENAI_API_KEY=sk-parley-v1-...
uv run agent.py --host https://parley.api.mit.edu/v1 --model claude-opus-5-5 "Are labs due in session?" --trace parley-claude.jsonl
uv run agent.py --host https://parley.api.mit.edu/v1 --model gpt-5.6-sol "Are labs due in session?" --trace parley-gpt.jsonl
```

`curl -H "Authorization: Bearer $OPENAI_API_KEY" https://parley.api.mit.edu/v1/models` lists the model names you can pass to `--model`. Two things to know:

- Your question and every line the tools retrieve leave your machine and go through the gateway to the provider. Use a file you are comfortable sending.
- `--think` is off by default and sends `reasoning_effort: none`. Hosted reasoning models may ignore it or charge for thinking anyway; add `--think` to let the model reason at its default effort. Each run of this agent costs a fraction of a cent on the models above, so the monthly credit covers a semester of this lab many times over. When it runs out mid-month, calls return a 402 until the next top-up.

The saved traces `example/lab-deadline-claude-opus-5-5.jsonl` and `example/lab-deadline-gpt-5.6-sol.jsonl` were made this way. That matters for reading them: the gateway returns the bare model's reply to our request, so the only harness in those traces is this repository's Python. Running the same question through Claude Code or the Codex CLI would put a second harness, with its own system prompt, tools, and retries, between our loop and the model, and the trace would not show which one made each decision. The harness and file tools still run on the laptop, so students need Python and the client but not the Ollama application or a model. The question and every retrieved excerpt travel to the server.

## Command-line options

Run `uv run agent.py --help` for the full interface.

| Option | Purpose | Default |
|---|---|---|
| `--file PATH` | Select one UTF-8 text file | Bundled `example/input.md` |
| `--model NAME` | Model name on the server | `qwen3:1.7b` |
| `--host URL` | OpenAI-compatible endpoint | `http://localhost:11434/v1` |
| `--api-key TOKEN` | API key; local Ollama ignores it | `$OPENAI_API_KEY`, else `none` |
| `--trace PATH` | Save full requests, responses, and events as JSONL; refuses to overwrite | No trace file |
| `--max-steps N` | Cap model calls, including corrective turns | 8 |
| `--search-only` | Remove the reader and its required-read check | Off |
| `--think` | Let the model think before answering; off sends `reasoning_effort: none` | Off |
| `--note TEXT` | Add a user message after the question, for example a rule to follow | None |
| `--compact N` | Every N steps, replace the history with a model-written summary; the trace records what was dropped | Off |
| `--stamp` | Put the current time at the top of the system prompt, which defeats the prefix cache between runs | Off |

Traces contain retrieved file text. The repository ignores `*.jsonl` outside `example/`, `runs/`, and `.venv/`.

Every response event carries `prompt_tokens` and `cached_tokens` as the server reported them, and the CLI prints them as a `[usage]` line. Ollama and OpenAI models report real numbers; OpenAI caches only prefixes above about a thousand tokens, so short runs show zero. Claude through Parley's OpenAI-compatible endpoint reports a few tokens per request, which is a translation artifact, not a measurement. Compaction requests appear in the trace with `"purpose": "compact"` and are followed by a `compact` event listing the dropped messages; `Evidence` keeps its own record across compaction, so the checks still accept citations to lines the model can no longer see.

## Tools

The operator selects the file, which is read into a fixed snapshot at startup. The model cannot supply paths, run shell commands, or write files.

- `search(query)`: every whitespace-separated term must occur as a case-insensitive substring of the line, in any order. Returns up to 12 matching lines with their line numbers and says whether more were cut off.
- `read_lines(start, end)`: an inclusive, 1-based range of at most 20 lines.
- Files are limited to 200,000 characters and lines to 1,000 characters.
- Unknown tools and invalid arguments return an error to the model.

These limits describe the tool interface, not an OS sandbox. Python runs with the operator's permissions.

## Checks before an answer is accepted

1. At least one valid search ran.
2. If no search returned lines, a second distinct search ran. After two empty searches, Python returns a fixed abstention instead of the model's answer.
3. If the reader is enabled, the lines read so far include some search hit together with its immediate neighbors.
4. The answer contains at least one `[L25]` or `[L25-L26]` citation, and every citation refers to returned lines.

A failed check appends feedback to the conversation and consumes one step of the budget. The checks do not establish that every claim is cited, that the cited passage supports the claim, or that the neighbors were enough context. An answer can cite real evidence while omitting an exception elsewhere in the file.

## Limits and stop reasons

Each model request sets an 8,192-token context, a 1,024-token output limit, and temperature 0, with a 120-second client timeout. Model support for these options varies.

| Stop reason | Meaning | Answer returned |
|---|---|---|
| `final_answer` | An answer passed the checks | The model's answer |
| `no_evidence_found` | Two searches found nothing | The fixed abstention |
| `step_limit` | `--max-steps` model calls used up | None, exit status 1 |
| `model_output_limit` | The model's response was truncated | None, exit status 1 |

An accepted answer is still a claim to check against the source.

There is no context compaction, retry on network errors, semantic citation check, or server authentication. A long history can exceed the context window, and temperature 0 does not guarantee identical output across machines or server versions.

## Saved traces

`example/` holds the input file and six complete traces, recorded 2026-10-12. The first four use `qwen3:1.7b` on Ollama 0.35.1 through its OpenAI-compatible endpoint; the last two use hosted models called directly through MIT's Parley gateway, so no vendor agent harness is involved. All at temperature 0 with thinking off. They are one run each, not the only possible run; a new model build can change them.

| File | Command |
|---|---|
| `late-penalty.jsonl` | `uv run agent.py "What is the penalty for a late submission?"` |
| `lab-deadline.jsonl` | `uv run agent.py "Are labs due in session?"` |
| `lab-deadline-search-only.jsonl` | `uv run agent.py --search-only "Are labs due in session?"` |
| `sick.jsonl` | `uv run agent.py "What should I do if I am sick?"` |
| `lab-deadline-claude-opus-5-5.jsonl` | `uv run agent.py --host https://parley.api.mit.edu/v1 --model claude-opus-5-5 "Are labs due in session?"` |
| `lab-deadline-gpt-5.6-sol.jsonl` | `uv run agent.py --host https://parley.api.mit.edu/v1 --model gpt-5.6-sol "Are labs due in session?"` |

Regenerate them after any change to the system prompt, tools, or options, with `--trace example/<name>.jsonl` after deleting the old file. A test checks that the saved traces still match the current prompt, tools, and options.

## Tests

```sh
uv run python -m unittest discover -s . -v
```

The tests use the standard library and fake model responses, so Ollama need not be running. They cover search semantics, line numbering, argument validation, message flow, the retrieval and citation checks, and stopping. They do not measure model quality.

## Testing a harness change

Keep the input file, question, LLM, and settings the same within each before-and-after comparison. For deadline questions, select `example/input.md`; a question about your own invented file may not exercise the change.

### Choose a change and test cases

- **Read limits.** Change a read limit or its tool description. Construct a call at the limit and check the returned lines or error. Test tool behavior rather than relying only on the final answer.
- **Compaction.** Change `COMPACT_PROMPT` after collecting a run that actually compacts. Try “What should I do if I am sick?” with `--compact 2 --note "Rule: answer entirely in capital letters."`. Look for a `compact` event and inspect the next request. If compaction never occurs, try one other question, then choose another area.
- **Answer checks.** Add an observable `Evidence` check, such as citation coverage for retrieved lines containing “except” or “however”. A test answer that omits the required citation should be handled differently. An answer that cites the exception but gives the wrong deadline can show the check's limit. Citation coverage does not verify the explanation.

Before running, predict both versions' results. If the test meant to expose the change would behave alike in both versions, revise it. The test of a remaining limitation may give the same result.

### Direct tool and answer checks

If the LLM never attempts the relevant tool call, test it with `FileTools.dispatch`. Save the direct output separately from LLM traces and explain which one exercises the change. The final answer need not change.

For direct answer checks, import `FileTools` and `Evidence` from `agent.py`. Create `files = FileTools("example/input.md")` and `evidence = Evidence(files)`. For each successful dispatch, pass the tool name, arguments, and returned line numbers to `evidence.record(...)`. Print `evidence.check(answer)`; `None` means accepted. Use identical tool calls and candidate answers before and after.

### Saved-trace consistency failures

Changes to prompts, tools, or options may fail `test_saved_traces_match_current_prompt_tools_and_options` because the bundled traces describe the original harness. During a lab experiment, preserve those traces and report the mismatch separately from behavioral failures. The regeneration instructions above are for maintaining the repository's examples, not for making an experimental change pass this test.

## References

- [OpenAI Python client](https://github.com/openai/openai-python), used for every server
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
- [Qwen3 8B](https://ollama.com/library/qwen3:8b)
