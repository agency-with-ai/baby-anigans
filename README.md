# Baby Anigans

**A tiny research assistant you can read end to end.**

Ask a question about a local file. Baby Anigans searches it, reads nearby lines, and answers with citations. The interesting part is what happens between the question and the answer: a model requests actions, and a short Python program carries them out.

By the end of this walkthrough, you should be able to point to the **model**, **tools**, **context**, and **harness** in a running agent.

Built for [Agency with AI](https://agencyai.mit.edu), MIT 6.S950. The [project spec](project-spec.md) follows Lab 3's questions about scope, a one-day version, and how to judge a result. It describes Baby Anigans itself; `spec.txt` is fictional source material for the assistant to read.

## 1. Give it a question

You need Python 3.10+ and [Ollama](https://ollama.com/download) running. These commands use a small local model, with a roughly 1.4 GB download. No Ollama account is needed.

```sh
# Repository access is required while this repo is private.
git clone git@github.com:agency-with-ai/baby-anigans.git
cd baby-anigans
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen3:1.7b

python agent.py "What should happen if the feed is unavailable?" \
  --model qwen3:1.7b --trace first-run.jsonl
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. If Ollama is not running in the background, run `ollama serve` in another terminal. For a larger model or a remote endpoint, see [setup options](docs/reference.md#model-options).

The question is about the fictional project described in [spec.txt](spec.txt). Open that file beside the answer. Does the cited line say what the answer claims?

The small model can make mistakes or reach the step limit. Keep its output: a failed run can still show us exactly how the system works.

## 2. Follow a search into the code

Look for a `[tool]` event in the terminal. A search request might look like:

```text
name: search
arguments: {"query": "feed unavailable"}
```

**The model has requested a search. It has not searched your disk.**

Open [agent.py](agent.py) and find these three pieces:

1. **`TOOLS`** describes `search` and its arguments. This is the interface sent to the model: a *tool schema*.
2. **`FileTools.dispatch`** receives the requested name and arguments and chooses an allowed Python function.
3. **`FileTools.search`** performs the search and returns numbered matches.

For this query, the tool returns:

```text
25: If the feed is unavailable, report the failure and write no shortlist.
```

The line number comes from Python, not from the model counting lines. Search is ordinary text matching: all query terms must occur on the same line, in any order. There is no embedding model or vector database.

**Before moving on:** where would you change what “search” means—the tool description, the Python function, or both?

## 3. Find out how the model sees the result

Find `run_agent`. Follow the `messages` list through one iteration:

```text
Question and instructions
          ↓
       Model call
          ↓
   Requested tool action
          ↓
  Python executes the tool
          ↓
 Result appended to messages
          ↓
     Next model call
```

The returned line becomes a **tool-result message**. That is how it reaches the model on the next call. The model can then request more information or propose an answer.

Open `first-run.jsonl` in your editor. Find the first two `request` records and compare their `messages`. The later request includes information the earlier one did not have. This growing input is the model's **context** for the run.

The file existed before either call. But the model did not receive its contents until a tool returned them. **Stored on disk, accessible through a tool, and present in context are different things.**

If you repeat the command, choose a new trace filename; the program will not overwrite an existing trace.

## 4. Why read after searching?

Now ask:

```sh
python agent.py "Are all screened entries marked read?" --model qwen3:1.7b
```

The source contains a rule and an exception:

```text
29: After a successful sweep, mark screened entries read.
30: Exception: leave borderline entries unread until the instructor reviews them.
```

A search can return line 29 without line 30. An answer based only on the match can therefore miss the exception.

The second tool, **`read_lines(start, end)`**, lets the model ask for surrounding text. Find its schema and implementation. Then inspect the run:

- Which words did the model search for?
- Did it retrieve the rule? The exception?
- If the answer was wrong or missing, was the evidence absent from the context, or mishandled after it arrived?

The small model sometimes includes “all” in its search and finds neither line. That is a poor query for this search function, not evidence that the file lacks an answer.

## 5. Where is the harness?

You may also have seen `[check]` events:

```text
Search the file before answering.
Read neighboring lines too, not only the match.
Cite the retrieved evidence using [L25] or [L25-L26].
```

These are **not model thoughts**. They come from checks in `run_agent`. When a proposed answer fails a check, Python appends corrective feedback and calls the model again, within a fixed call budget.

This surrounding program is the **harness**. It constructs context, dispatches actions, returns observations, checks the proposed answer's form, and decides whether to continue or stop. Ollama is the **model server**; it supplies the model responses. The model server and the harness are separate programs.

Contrast two lines of defense in `agent.py`:

- `SYSTEM` asks the model to cite evidence.
- Python checks that citations refer to lines the tools returned.

The first is an instruction. The second enforces a limited property. **Neither proves that the cited passage supports the conclusion.**

For a short file like this one, putting the entire numbered file into one prompt might be simpler. We use tools here to expose how an agent obtains information over several calls.

## 6. Change one component

Choose a comparison, predict what will change, then inspect the trace.

**Keep the harness; change the model.**

```sh
ollama pull qwen3:8b
python agent.py "Are all screened entries marked read?" --model qwen3:8b
```

This model needs more memory. Does it choose different searches? Need fewer corrections? Include the exception?

**Keep the model; remove a tool.**

```sh
python agent.py "Are all screened entries marked read?" \
  --model qwen3:1.7b --search-only
```

This removes `read_lines` and the requirement to use it. The model might still find the exception through another search; removing the reader does not guarantee failure.

**Keep both; change the evidence.**

```sh
python agent.py "Your question" --model qwen3:1.7b --file /path/to/your-notes.txt
```

Use a nonsensitive UTF-8 text file and a question whose answer you can check. Then ask something the file does not answer. Does the agent distinguish finding no evidence from establishing that no answer exists?

## Next

- [Reference](docs/reference.md): hardware, remote inference, options, limits, and tests.
- [Source](agent.py): the entire application, without an agent framework.
- [Tests](test_agent.py): checks of the harness using fake model responses, not an assessment of model quality.

[MIT license](LICENSE).
