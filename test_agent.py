import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from agent import OPTIONS, SYSTEM, TOOLS, FileTools, run_agent


class FakeClient:
    def __init__(self, messages, reason="stop"):
        self.messages = iter(messages)
        self.requests = []
        self.reason = reason

    def chat(self, **request):
        self.requests.append(copy.deepcopy(request))
        message = next(self.messages)
        return SimpleNamespace(
            message=SimpleNamespace(model_dump=lambda **kwargs: message),
            done_reason=self.reason,
        )


def call(name, arguments):
    return {"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": name, "arguments": arguments}}
    ]}


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.files = FileTools(Path(__file__).parent / "example" / "input.md")
        self.events = []

    def emit(self, event, data):
        self.events.append((event, copy.deepcopy(data)))

    def test_search_returns_actual_line_numbers(self):
        result, numbers = self.files.search("PENALIZED")
        self.assertEqual(result["total_matches"], 1)
        number, text = result["lines"].split(": ", 1)
        self.assertEqual(self.files.lines[int(number) - 1], text)
        self.assertEqual(numbers, {int(number)})

    def test_search_matches_terms_in_any_order(self):
        self.assertIn("125:", self.files.search("submission late")[0]["lines"])

    def test_rejects_unseen_or_missing_citations(self):
        for answer in ("Failure.", "Failure. [L999]", "Failure. [L24-L25]"):
            client = FakeClient([call("search", {"query": "unavailable"}),
                                 {"role": "assistant", "content": answer}])
            self.assertIsNone(run_agent(client, "fake", "Question", self.files, self.emit,
                                        max_steps=2, search_only=True))
            self.assertEqual(self.events[-1][1]["reason"], "step_limit")

    def test_requires_neighbors_not_just_match(self):
        for start, end, accepted in [(50, 50, False), (1, 3, False), (49, 51, True)]:
            client = FakeClient([call("search", {"query": "due in session"}),
                                 call("read_lines", {"start": start, "end": end}),
                                 {"role": "assistant", "content": "Rule. [L50]"}])
            result = run_agent(client, "fake", "Question", self.files, self.emit, max_steps=3)
            self.assertEqual(result is not None, accepted)

    def test_no_search_no_answer(self):
        client = FakeClient([{"role": "assistant", "content": "No evidence."}])
        self.assertIsNone(run_agent(client, "fake", "Question", self.files, self.emit, max_steps=1))

    def test_no_evidence_returns_harness_abstention(self):
        client = FakeClient([call("search", {"query": "xyzzy"}),
                             call("search", {"query": "plugh"}),
                             {"role": "assistant", "content": "Invented answer."}])
        answer = run_agent(client, "fake", "Question", self.files, self.emit)
        self.assertIn("could not find", answer)
        self.assertNotIn("Invented", answer)

    def test_no_match(self):
        self.assertEqual(self.files.search("xyzzy")[0]["total_matches"], 0)

    def test_inclusive_read(self):
        self.assertEqual(self.files.read_lines(1, 2), ({"lines": "1: # 6.390 Introduction to Machine Learning, Fall 2026\n2: "}, {1, 2}))

    def test_invalid_calls_are_errors(self):
        for name, args in [("shell", {}), ("search", {"query": ""}),
                           ("search", {"query": "feed", "path": "/etc/passwd"}),
                           ("read_lines", {"start": 0, "end": 3}),
                           ("read_lines", {"start": True, "end": 3}),
                           ("read_lines", {"start": 1, "end": 21})]:
            with self.subTest(name=name, args=args):
                self.assertIn("error", self.files.dispatch(name, args)[0])

    def test_tool_result_reaches_next_call(self):
        client = FakeClient([call("search", {"query": "penalized"}),
                             {"role": "assistant", "content": "Not penalized. [L136]"}])
        answer = run_agent(client, "fake", "What if it fails?", self.files, self.emit,
                           search_only=True)
        self.assertIn("Not penalized", answer)
        result = client.requests[1]["messages"][-1]
        self.assertEqual(result["role"], "tool")
        self.assertIn("penalized", json.loads(result["content"])["lines"])
        self.assertEqual(len(client.requests[0]["messages"]), 2)

    def test_search_only_removes_and_blocks_reader(self):
        client = FakeClient([call("read_lines", {"start": 1, "end": 2})])
        self.assertIsNone(run_agent(client, "fake", "Question", self.files, self.emit,
                                    max_steps=1, search_only=True))
        self.assertEqual(len(client.requests[0]["tools"]), 1)
        tool = next(data for event, data in self.events if event == "tool")
        self.assertIn("error", tool["result"])
        self.assertEqual(self.events[-1][1]["reason"], "step_limit")

    def test_truncated_answer_is_not_accepted(self):
        client = FakeClient([{"role": "assistant", "content": "Partial"}], reason="length")
        self.assertIsNone(run_agent(client, "fake", "Question", self.files, self.emit))
        self.assertEqual(self.events[-1][1]["reason"], "model_output_limit")


class SavedTraceTests(unittest.TestCase):
    """The traces in example/ must describe the code as it is now."""

    def test_saved_traces_match_current_prompt_tools_and_options(self):
        paths = sorted((Path(__file__).parent / "example").glob("*.jsonl"))
        self.assertEqual([p.name for p in paths], ["lab-deadline-search-only.jsonl", "lab-deadline.jsonl",
                                                   "late-penalty.jsonl", "sick.jsonl"])
        for path in paths:
            rows = [json.loads(line) for line in path.open(encoding="utf-8")]
            with self.subTest(trace=path.name):
                self.assertEqual(rows[0]["event"], "request")
                self.assertEqual(rows[-1]["event"], "stop")
                for row in rows:
                    if row["event"] == "request":
                        self.assertEqual(row["messages"][0], {"role": "system", "content": SYSTEM})
                        self.assertEqual(row["options"], OPTIONS)
                        names = {tool["function"]["name"] for tool in row["tools"]}
                        self.assertTrue(names <= {tool["function"]["name"] for tool in TOOLS})


if __name__ == "__main__":
    unittest.main()
