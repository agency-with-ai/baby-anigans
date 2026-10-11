# Baby Anigans

**A tiny research assistant you can read end to end.**

A local-file Q&A agent for learning how models, tools, context, and a harness fit together. It uses Ollama to search a file, read surrounding lines, and answer with supporting line citations.

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. The point is to see the machinery: no agent framework, embeddings, or vector database.

## Setup

You need Python 3.10+, [Ollama](https://ollama.com/download), and a model that supports tool calling. No Ollama account is needed for local inference with public models.

```sh
# Repository access is required while this repo is private.
git clone git@github.com:agency-with-ai/baby-anigans.git
cd baby-anigans
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:8b
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead. Make sure Ollama is running; on installations without a background service, start `ollama serve` in another terminal.

Qwen3 8B is the configurable default. Local smoke tests exercise the loop, but it still misses evidence and instructions; it is not a reliable classroom baseline yet. Its download is about 5 GB and inference needs additional memory. A smaller tool-capable model may run on lighter hardware but make more mistakes. Select another installed model with `--model`.

## Local toy or larger model

The same harness can use a smaller local model:

```sh
ollama pull qwen3:1.7b
python agent.py "What should happen if the feed is unavailable?" --model qwen3:1.7b
```

Qwen3 1.7B downloads about 1.4 GB. On an M4 Max Studio, Ollama reported 2.4 GB loaded with our 8K context configuration. Allow additional RAM for the OS and applications; student-laptop performance has not been measured.

This is a **toy model for seeing the loop run**, not a reliable answerer. In three local runs of the feed question it searched, read neighboring lines, and cited L25 correctly after harness corrections. It failed to find the screened-entry exception with its chosen searches, and hit the step cap on the deployment question because it repeatedly cited unseen lines. The absent-budget question produced the harness's qualified abstention. The model and task were not changed to hide these failures.

For a larger local model, use `--model qwen3:8b`. For a course-provided remote endpoint, use `--host URL --model MODEL`; students then need Python and this client package, not the Ollama application or a model download. No course endpoint is configured yet. Any endpoint requiring authentication also needs client credential configuration, which this CLI does not yet expose.

## Ask a question

```sh
python agent.py "What should happen if the feed is unavailable?" --trace run.jsonl
```

By default, the agent uses the included fictional `spec.txt`. To use your own UTF-8 text file:

```sh
python agent.py "Your question" --file /path/to/document.txt
```

The terminal shows executed tool requests, results, the stopping reason, and the final answer. `--trace` saves complete model requests and responses as JSONL, including tool definitions and returned text. It refuses to overwrite an existing file; choose a new name for another run.

Other questions to try:

```sh
python agent.py "Are all screened entries marked read?"
python agent.py "What exact deployment machine has been selected?"
python agent.py "Are all screened entries marked read?" --search-only
```

`--search-only` disables the surrounding-line reader in both the tool definitions and the dispatcher. It need not make the answer wrong: the model may find the same information through another search.

## Where is the harness?

Open `agent.py`:

- **`TOOLS`** describes the two tool interfaces to the model.
- **`FileTools`** implements case-insensitive all-query-terms search and inclusive, numbered line reads over a fixed file snapshot.
- **`dispatch`** validates the requested tool and arguments, then calls the Python function. A model request does not execute itself.
- **`run_agent`** is the loop: assemble messages → call the model → execute requested tools → append their results → call the model again.
- **`main`** connects the client, command-line options, and trace output.

Ollama serves the model. Python runs the harness and tools. The model does not see the whole file automatically: it receives the excerpts returned by tool calls. For a short file, putting the entire numbered file in one prompt may be simpler; this example exists to expose the retrieval loop.

## Model responses are not guarantees

The harness rejects a final answer before a search, asks for another keyword after a first empty search, and requires reading a matched line with its immediate neighbors (unless `--search-only`). When evidence was returned, it requires at least one citation and checks that every recognized citation refers to returned lines. Corrections appear as `[check]` events and consume the same bounded call budget. After two distinct searches with no returned lines, the harness supplies a fixed, qualified abstention rather than accepting invented content.

These checks enforce a small retrieval procedure, not correctness. They do not establish that each claim has a citation, that the cited passage supports it, or that all relevant evidence was found. Reading immediate neighbors does not guarantee sufficient context. Check the answer against the source.

Before these checks were added, local Qwen3 8B tests found premature answers after an unsuccessful literal search and a missed exception immediately after a matching line. An explicit request to search for `screened` and use `read_lines` retrieved the exception and produced a cited answer. Enabling `--think` did not consistently fix the problems. After the checks and all-query-terms search were added, the original feed-failure, read-status, and deployment questions returned correct cited answers in local smoke runs. The read-status answer included the exception. These are smoke tests, not a reliability benchmark.

An initial live test with `gpt-oss:20b` retrieved the relevant passage and answered correctly but omitted citations. A `llama3.2` run misinterpreted a tool error as document evidence. Those are individual observations, not model benchmarks. Rehearse your chosen model on your questions.

`--max-steps` caps model calls (default 8). Each response can request at most eight tools. Invalid calls return errors to the model. Output truncation and reaching the step cap stop the run without presenting it as completed. Calls have a 120-second client timeout. The request uses an 8,192-token context, a 1,024-token output limit, and `think=False` by default. Use `--think` to compare with thinking enabled; support and behavior can vary by model.

This simple version has no context compaction, network retries, semantic citation verifier, or service authentication.

## Local tools, local or remote inference

```sh
python agent.py "Your question" --host http://localhost:11434 --model qwen3:8b
```

Changing `--host` changes the model server, not where the file tools run. With remote inference, your question and retrieved excerpts leave your machine. Trace files also contain those excerpts. Do not use sensitive files unless the deployment is appropriate for them.

The model cannot select arbitrary paths or request shell commands through these tools. The operator selects one file, read once at startup. This is not an OS sandbox: the Python process still has your permissions. Do not expose a raw, unauthenticated Ollama endpoint publicly.

To keep the demo bounded, files may contain at most 200,000 characters and lines at most 1,000 characters. Search returns up to 12 matches; the reader returns up to 20 lines per call. Growing history can still exceed the context window.

## Test without a model

```sh
python3 -m unittest discover -s . -v
```

The tests use fake model responses to check tool behavior, message flow, and stopping rules. They require only the Python standard library, not a running model. They test the harness, not model quality.

## References

- [Ollama Python client](https://github.com/ollama/ollama-python)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Qwen3 8B](https://ollama.com/library/qwen3:8b)

## License

[MIT](LICENSE).
