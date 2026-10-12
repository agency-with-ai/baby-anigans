# Running Baby Anigans

Setup, models, flags, limits, and tests. The [README](../README.md) walks through one run of the loop. A person or a coding agent should be able to follow this page without further context.

## Setup

Requires Python 3.10+ and [Ollama](https://ollama.com/download). No Ollama account is needed, and after the model download everything runs offline.

```sh
git clone git@github.com:agency-with-ai/baby-anigans.git
cd baby-anigans
python3 -m venv .venv && source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:1.7b
python agent.py "What should happen if the feed is unavailable?" --trace first-run.jsonl
```

If Ollama is not already running, start `ollama serve` in another terminal. `requirements.txt` pins the Python client (`ollama==0.6.3`), not the Ollama server or the model weights.

## Models

| Model | Download | Memory when loaded |
|---|---|---|
| `qwen3:1.7b` (default) | 1.4 GB | 2.4 GB |
| `qwen3:8b` | 5.2 GB | 6.6 GB |

Memory is what Ollama reported on our M4 Max Studio at the configured 8K context; allow extra for the OS and other applications. We have not measured student laptops. A 16 GB laptop is a planning target for the larger model, not a tested minimum.

The default is a toy for inspecting the loop. It can choose poor search queries, miss evidence, or fail the citation checks, and completing one question says nothing about the next. `--model qwen3:8b` answered the feed-failure, exception, and deployment questions with citations in local smoke runs; correctness is still not guaranteed.

`--host https://agencyai.mit.edu/ollama --api-key TOKEN` sends model calls to the course server instead, with the token handed out in class. `OLLAMA_API_KEY=TOKEN` in the environment does the same. The harness and file tools still run on the laptop, so students need Python and the client but not the Ollama application or a model. The question and every retrieved excerpt travel to the server. The server is shared and CPU-only, so expect slower answers when many people use it at once.

## Command-line options

Run `python agent.py --help` for the full interface.

| Option | Purpose | Default |
|---|---|---|
| `--file PATH` | Select one UTF-8 text file | Bundled `docs/example-input.txt` |
| `--model NAME` | Select an installed model | `qwen3:1.7b` |
| `--host URL` | Select the model server | `http://localhost:11434` |
| `--api-key TOKEN` | Bearer token for a shared server | `$OLLAMA_API_KEY` |
| `--trace PATH` | Save full requests, responses, and events as JSONL; refuses to overwrite | No trace file |
| `--max-steps N` | Cap model calls, including corrective turns | 8 |
| `--search-only` | Remove the reader and its required-read check | Off |
| `--think` | Enable thinking for a model that supports it | Off |

Traces contain retrieved file text. The repository ignores `*.jsonl`, `runs/`, and `.venv/`.

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

## Tests

```sh
python -m unittest discover -s . -v
```

The 12 tests use the standard library and fake model responses, so Ollama need not be running. They cover search semantics, line numbering, argument validation, message flow, the retrieval and citation checks, and stopping. They do not measure model quality.

## References

- [Ollama Python client](https://github.com/ollama/ollama-python)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
- [Qwen3 8B](https://ollama.com/library/qwen3:8b)
