# Baby Anigans: project spec

## Scope, users, and ideal result

Baby Anigans is a small research assistant for students learning how an agent works. It answers one question about one local text file using a model and two read-only tools: search for lines and read a range of lines.

Its first purpose is to make the mechanism understandable, not to outperform document-Q&A services. A student should be able to trace how the question reaches the model, how a requested action becomes a Python function call, how returned text enters the next model call, and why the harness continues or stops.

The ideal result is a concise answer supported by accurate line citations, together with a record that lets the reader inspect how it was produced. A useful teaching run can also end in failure, provided the record makes that failure inspectable. We assess answer quality separately from understanding the mechanism.

## A one-day version

Keep:

- One question per invocation and one operator-selected UTF-8 text file.
- A small Python harness with an explicit model/tool loop.
- Two bounded tools: search and read numbered lines. The model cannot choose another file or execute shell commands.
- A local model connection, with the endpoint and model configurable.
- Visible tool requests, returned evidence, corrective checks, and the stopping reason. Optionally save the full model requests and responses.
- A finite call budget. Reject unsupported tool names, invalid arguments, and citations to lines that were not returned.

Leave out interactive chat, multiple documents, web browsing, embeddings, persistent memory, skills, subagents, and automatic editing of files. These are possible later extensions, not prerequisites for understanding the first loop.

Try the supplied fictional feed-project file first. Ask what should happen when its feed is unavailable. Then ask about a rule with an exception on the following line, and about information the file does not supply.

Judge usefulness in two ways:

1. **Mechanism:** with AI closed, a student can follow a tool request through the dispatcher and identify the returned text in the next model request. They can predict what information is unavailable if the surrounding-line reader is removed. Removing it need not cause failure: another search could retrieve the same evidence.
2. **Answer:** a reader checks the final claims and citations against the source, including qualifications and exceptions. A successful process exit or a valid citation number is not enough.

## What already exists, and what is different here?

A single model call containing the entire numbered file could solve this small task more simply. Chat products also offer document Q&A. Neither requires the reader to examine the retrieval and execution loop.

The [Ollama tool-calling examples](https://docs.ollama.com/capabilities/tool-calling) demonstrate the model interface. [Mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) offers a readable implementation of a more capable agent. Baby Anigans uses a narrower, non-coding task with evidence that students can inspect directly. Its contribution is the teaching example and walkthrough, not a new retrieval algorithm or an agent-performance claim.

## What involves reading, and what involves building?

Reading work includes understanding the model API, how tool requests and results are represented, and the distinction between prompting a behavior and enforcing an observable condition. Read the source passages used to assess each answer rather than relying on the agent's summary.

Building work includes the tools, dispatcher, message loop, trace output, limits, and tests. Model training and serving are supplied by existing software. No claim of learning follows merely from successfully running the finished program; students need to explain or modify the mechanism themselves.

## A concrete request and acceptable results

**Request:** “Are all screened entries marked read?”

The sample file gives a general rule—mark screened entries read after a successful sweep—and an exception: leave borderline entries unread until instructor review.

An acceptable substantive answer states the rule with that exception and cites the supporting lines. “No, borderline entries remain unread until review” and “Screened entries are marked read after a successful sweep, except borderline entries awaiting review” can both be acceptable. An unconditional “Yes, all screened entries are marked read” is not.

Work through the case by hand:

1. A search for `screened entries` finds the general rule but not necessarily the exception.
2. Reading the neighboring line reveals the exception.
3. The answer must preserve that qualification. A citation to the general rule alone does not justify a universal conclusion.

This case motivates a neighboring-line read before accepting an evidence-based answer. That check is limited: exceptions may appear farther away, and the model may misinterpret text it receives. The harness cannot certify semantic support by checking line numbers.

If the model searches poorly and finds nothing, the program may report that its searches found no supporting lines. That is an honest retrieval failure, not a correct substantive answer to this case. If the run reaches a limit, it must report an incomplete run rather than present an unchecked answer as successful.

For a question whose answer is absent, such as the exact monthly hosting budget, do not invent a number. Describe the lack of retrieved support without claiming that a few unsuccessful searches prove absence.

## Challenges and open questions

- **Small-model behavior:** how often do intended student models complete the loop and answer correctly? Keep the same questions and harness when comparing models. Existing smoke runs are not reliability estimates.
- **Hardware:** what installation, memory use, and response time should students expect on their laptops? Studio measurements do not settle this.
- **Retrieval:** when is keyword search sufficient, and when does it miss relevant phrasing or distant qualifications? Compare against the simpler whole-file baseline before adding retrieval machinery.
- **Scaffolding:** how many corrective checks help students see the loop, and when do they obscure it? The current checks enforce observable procedure, not understanding.
- **Learning:** does tracing and modifying this small agent improve students' ability to diagnose another agent? Published work on code comprehension and learning with AI may help choose an assessment; a successful demo does not answer the question.
- **Deployment:** local inference is available; a shared class endpoint, authentication, and concurrency capacity remain undecided. Remote requests would include retrieved file excerpts.

## Review the spec

Have a reader propose another concrete request and describe an acceptable result before showing them the implementation. Compare their interpretation with this spec. Record disagreements and revisions rather than assuming that several successful examples establish shared understanding.

No partner review or student learning assessment is claimed by this document. Those checks remain to be done.
