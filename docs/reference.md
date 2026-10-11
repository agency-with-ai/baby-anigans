# Running Baby Anigans

Start with the [walkthrough](../README.md) to learn the loop. This page collects setup choices and implementation limits.

## Model options

### Small local model

Install [Ollama](https://ollama.com/download), start it, and download the model:

```sh
ollama pull qwen3:1.7b
python agent.py "What should happen if the feed is unavailable?" --model qwen3:1.7b
```

The download is about 1.4 GB. Ollama reported 2.4 GB loaded on our M4 Max Studio at the configured 8K context. Allow extra memory for the OS and other applications. We have not measured student-laptop performance.

This is a toy model for inspecting the loop. It can choose poor search queries, miss evidence, or fail the citation checks. Completing one question does not establish reliability on others.

### Larger local model

```sh
ollama pull qwen3:8b
python agent.py "Are all screened entries marked read?" --model qwen3:8b
```

This is the code's default model when `--model` is omitted. The download is about 5.2 GB; Ollama reported 6.6 GB loaded on the Studio. A 16 GB laptop is a reasonable planning target, not a tested minimum. Local smoke runs answered the feed-failure, exception, and deployment questions with citations under the current harness; correctness is not guaranteed.

Local inference needs no Ollama account and can run offline after installation and model download.

### Remote inference

```sh
python agent.py "Your question" --host https://YOUR-ENDPOINT --model MODEL
```

Students need Python and the Python client, but not the Ollama application or a downloaded model. The harness and file tools still run on the laptop. Questions and retrieved file excerpts travel to the model server.

No course endpoint is configured yet. The CLI does not expose API-key configuration. Do not expose an unauthenticated Ollama server publicly merely to make this command work.

## Python dependency

```sh
python -m pip install -r requirements.txt
```

`requirements.txt` pins `ollama==0.6.3`, the Python client version used for our local tests. It does not pin the Ollama server, model weights, or transitive Python dependencies. The README recommends Python 3.10+; the initial local smoke tests used Python 3.9, so they do not establish a cross-version compatibility matrix.

## Command-line options

Run `python agent.py --help` for the full interface.

| Option | Purpose | Default |
|---|---|---|
| `--file PATH` | Select one UTF-8 text file | Bundled `spec.txt` |
| `--model NAME` | Select an installed model | `qwen3:8b` |
| `--host URL` | Select the model server | `http://localhost:11434` |
| `--trace PATH` | Save full requests, responses, and events as JSONL | No trace file |
| `--max-steps N` | Cap model calls, including corrective turns | 8 |
| `--search-only` | Remove the reader and its required-read check | Off |
| `--think` | Enable thinking for a model that supports it | Off |

Trace files must not already exist. They include retrieved text and can contain sensitive information. The repository ignores JSONL traces, `runs/`, and the virtual environment.

## Tools and boundaries

The operator selects the file, which is read into a fixed snapshot at startup. The model cannot supply paths, execute shell commands, or write files through the tools.

- `search(query)` requires every whitespace-separated query term to occur as a case-insensitive substring on a line, in any order. It returns up to 12 matching lines with their original line numbers and indicates whether results were truncated.
- `read_lines(start, end)` returns an inclusive, 1-based range of at most 20 lines.
- Files are limited to 200,000 characters; individual lines to 1,000 characters.
- Unknown tools and invalid arguments return errors to the model.

These restrictions describe the available tool interface, not an OS sandbox. Python still runs with the operator's permissions.

## What the answer checks establish

Before accepting a proposed final answer, the harness checks that:

1. At least one valid search occurred.
2. If no lines were found, a second distinct search was attempted. After two unsuccessful searches, Python returns a fixed, qualified abstention.
3. If lines were found and the reader is enabled, a read included a previously retrieved line and its immediate neighbors where they exist.
4. An evidence-based answer contains at least one recognized `[L25]` or `[L25-L26]` citation, and every recognized citation refers to returned lines.

A failed check appends feedback and consumes the same bounded model-call budget. The checks do not establish that every claim is cited, that the passage supports the claim, or that immediate neighbors provide sufficient context. In particular, an answer can cite real evidence while omitting an important exception elsewhere.

## Limits and stopping

Each model response may request at most eight tools. The model request sets an 8,192-token context, a 1,024-token output limit, and temperature 0. The client timeout is 120 seconds. Model support for options can vary.

Reaching the call cap, receiving a truncated model response, or other unsuccessful termination does not count as a completed answer. An accepted answer is still a claim to check against the source.

There is no context compaction, network retry policy, semantic citation verifier, or service authentication. Growing history can exceed the context window. Temperature 0 does not guarantee reproducibility across machines or model-server versions.

## Test the harness without a model

```sh
python -m unittest discover -s . -v
```

The 12 tests use Python's standard library and fake model responses; they do not require Ollama to be running. They check search semantics, line numbering, validation, message flow, retrieval requirements, citation checks, and stopping behavior. They do not measure model quality.

## API references

- [Ollama Python client](https://github.com/ollama/ollama-python)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
- [Qwen3 8B](https://ollama.com/library/qwen3:8b)
