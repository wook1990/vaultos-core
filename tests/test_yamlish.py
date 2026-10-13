import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vaultos_core import yamlish  # noqa: E402
from vaultos_core.yamlish import YamlError, loads  # noqa: E402


class Parse(unittest.TestCase):
    def test_tracker_shape(self):
        text = """# header
tasks:
  - id: T-1
    title: "Login: Google"   # comment
    status: done
    requirement_ids: [REQ-A-001, "REQ-A-002"]
    evidence:
      - tests/test_login.py
    done_at: 2026-10-13
  - id: T-2
    title: 'it''s fine'
    evidence: []
    owner: null
"""
        d = loads(text)
        self.assertEqual(d["tasks"][0]["title"], "Login: Google")
        self.assertEqual(d["tasks"][0]["requirement_ids"], ["REQ-A-001", "REQ-A-002"])
        self.assertEqual(d["tasks"][0]["evidence"], ["tests/test_login.py"])
        self.assertEqual(d["tasks"][0]["done_at"], "2026-10-13")
        self.assertEqual(d["tasks"][1]["title"], "it's fine")
        self.assertEqual(d["tasks"][1]["evidence"], [])
        self.assertIsNone(d["tasks"][1]["owner"])

    def test_list_at_key_indent(self):
        self.assertEqual(loads("a:\n- x\n- y\nb: 1"), {"a": ["x", "y"], "b": "1"})

    def test_nested_map(self):
        self.assertEqual(loads("p:\n  q:\n    r: s\n"), {"p": {"q": {"r": "s"}}})

    def test_scalars(self):
        d = loads("a: null\nb: ~\nc:\nd: true\ne: false\nf: {}\ng: 12")
        self.assertEqual(d, {"a": None, "b": None, "c": None, "d": True, "e": False, "f": {}, "g": "12"})

    def test_hash_inside_quotes(self):
        self.assertEqual(loads('x: "a \\"b\\" # c" # real'), {"x": 'a "b" # c'})

    def test_empty(self):
        self.assertEqual(loads("# only a comment\n\n"), {})


class Reject(unittest.TestCase):
    CASES = {
        "a: b: c": 1, "a: |\n  x": 1, "a:\n\t- x": 2, "a: [1, [2]]": 1, "a: 1\na: 2": 2,
        "- x\nb: 1": 2, "a: 'x": 1, "a: {b: 1}": 1, "a: &x 1": 1, "a: 1\n---\nb: 2": 2,
        "  a: 1": 1, "a: [x, , y]": 1, "a:\n  - x\n    y: 1": 3,
    }

    def test_errors_have_lines(self):
        for text, line in self.CASES.items():
            with self.subTest(text=text):
                with self.assertRaises(YamlError) as cm:
                    loads(text)
                self.assertEqual(cm.exception.line, line)


class RoundTrip(unittest.TestCase):
    VALUES = ['he said: "x" # y\\z', "a'b", "tab\there", "line\nbreak", "  pad ", "#hash",
              "- dash", "[x]", "null", "true", "REQ-A-001", "한글 값", "x,y", ""]

    def test_quote(self):
        for v in self.VALUES:
            with self.subTest(v=v):
                self.assertEqual(loads("a: " + yamlish.quote(v))["a"], v)

    def test_flow(self):
        for v in self.VALUES:
            if v == "":
                continue
            with self.subTest(v=v):
                self.assertEqual(loads("a: " + yamlish.flow([v, "plain"]))["a"], [v, "plain"])
        self.assertEqual(yamlish.flow(["REQ-A-001", "T-1"]), "[REQ-A-001, T-1]")
        self.assertEqual(loads("a: " + yamlish.flow([]))["a"], [])


if __name__ == "__main__":
    unittest.main()
