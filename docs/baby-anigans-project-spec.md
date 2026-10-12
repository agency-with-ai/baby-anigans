# Baby Anigans: project spec

## Scope, users, and ideal result

Baby Anigans is a small research assistant for students learning how an agent works. It answers one question about one local text file using a model and two read-only tools: search for lines and read a range of lines.

Its purpose is to make the mechanism understandable, not to outperform document-Q&A services. A student should be able to trace how the question reaches the model, how a requested action becomes a Python function call, how the returned text enters the next model call, and why the harness continues or stops.

The ideal result is a concise answer with accurate line citations, plus a record that lets the reader inspect how it was produced. A teaching run can also end in failure, provided the record makes that failure inspectable. Answer quality and understanding of the mechanism are assessed separately.

## A one-day version

Keep:

- One question per invocation and one operator-selected UTF-8 text file.
- A small Python harness with an explicit model/tool loop and a finite call budget.
- Two bounded tools: search and read numbered lines. The model cannot choose another file or run shell commands.
- A local model connection with a configurable endpoint and model.
- Visible tool requests, returned evidence, corrective checks, and the stopping reason, with an optional full trace of model requests and responses.
- Rejection of unsupported tool names, invalid arguments, and citations to lines that were not returned.

Leave out interactive chat, multiple documents, web browsing, embeddings, persistent memory, skills, subagents, and automatic file editing. These are possible later extensions, not prerequisites for understanding the first loop.

Try the supplied fictional feed-project file first. Ask what should happen when its feed is unavailable, then about a rule with an exception on the following line, then about information the file does not supply.

Judge usefulness in two ways:

1. **Mechanism:** with AI closed, a student can follow a tool request through the dispatcher and identify the returned text in the next model request. They can predict what information is unavailable if the surrounding-line reader is removed. Removing it need not cause failure: another search could retrieve the same evidence.
2. **Answer:** a reader checks the final claims and citations against the source, including qualifications and exceptions. A successful exit or a valid citation number is not enough.

## What already exists, and what is different here?

A single model call containing the entire numbered file could solve this small task more simply, and chat products offer document Q&A. Neither requires the reader to examine the retrieval and execution loop.

The [Ollama tool-calling examples](https://docs.ollama.com/capabilities/tool-calling) demonstrate the model interface. [Mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) is a readable implementation of a more capable agent. Baby Anigans uses a narrower, non-coding task whose evidence students can inspect directly. Its contribution is the teaching example and walkthrough, not a retrieval algorithm or a performance claim.

## What involves reading, and what involves building?

Reading: the model API, how tool requests and results are represented, and the difference between prompting a behavior and enforcing an observable condition. Read the source passages behind each answer rather than the agent's summary of them.

Building: the tools, dispatcher, message loop, trace output, limits, and tests. Model training and serving come from existing software. Running the finished program is not evidence of learning; students need to explain or modify the mechanism themselves.

## A concrete request and acceptable results

**Request:** "Are all screened entries marked read?"

The sample file gives a general rule, mark screened entries read after a successful sweep, and an exception: leave borderline entries unread until the instructor reviews them.

An acceptable answer states the rule with that exception and cites the supporting lines. "No, borderline entries remain unread until review" and "Screened entries are marked read after a successful sweep, except borderline entries awaiting review" are both acceptable. An unconditional "Yes" is not.

By hand:

1. A search for `screened entries` finds the general rule but not the exception.
2. Reading the neighboring line reveals the exception.
3. The answer must keep that qualification. A citation to the rule alone does not justify a universal conclusion.

This case motivates the neighboring-line read before an evidence-based answer is accepted. The check is limited: exceptions may appear farther away, the model may misread text it receives, and the harness cannot certify semantic support by checking line numbers.

If the model searches poorly and finds nothing, the program reports that its searches found no supporting lines. That is an honest retrieval failure, not a correct answer. If the run hits a limit, it must report an incomplete run rather than present an unchecked answer as successful. For a question the file does not answer, such as the monthly hosting budget, the agent must not invent one, and must not claim that a few failed searches prove absence.

## Challenges and open questions

- **Small-model behavior:** how often do the intended student models complete the loop and answer correctly? Compare models on the same questions and harness; smoke runs are not reliability estimates.
- **Hardware:** what installation, memory use, and response time should students expect on their laptops? Studio measurements do not settle this.
- **Retrieval:** when is keyword search sufficient, and when does it miss relevant phrasing or distant qualifications? Compare against the whole-file baseline before adding retrieval machinery.
- **Scaffolding:** how many corrective checks help students see the loop, and when do they obscure it? The current checks enforce observable procedure, not understanding.
- **Learning:** does tracing and modifying this agent improve students' ability to diagnose another agent? Work on code comprehension and learning with AI may help choose an assessment; a successful demo does not answer the question.
- **Deployment:** local inference works, and a shared CPU-only course server with a class token exists. How many students it can serve at once, and how slow it gets under load, remain unmeasured. Remote requests include retrieved file excerpts.

## Review the spec

Have a reader propose another concrete request and describe an acceptable result before seeing the implementation. Compare their interpretation with this spec, and record disagreements and revisions rather than assuming that a few successful examples establish shared understanding.

No partner review or student learning assessment is claimed here. Those checks remain to be done.
