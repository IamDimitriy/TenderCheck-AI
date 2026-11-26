import json
from pathlib import Path
import unittest

from verify import audit, build_index, check_reference


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads(Path(__file__).with_name("example.json").read_text(encoding="utf-8"))
        self.pages = build_index(self.case["pages"])
        self.claim = self.case["claims"][0]

    def test_example(self):
        results = audit(self.case)
        self.assertEqual([(item["status"], item["matched_pages"]) for item in results],
                         [("verified", [2]), ("wrong_page", [3]), ("unverified", [])])

    def test_wrong_document_is_not_evidence(self):
        changed = {**self.claim, "document": "График работ"}
        self.assertEqual(check_reference(changed, self.pages), ("unverified", []))

    def test_different_amount_is_not_evidence(self):
        changed = {**self.claim, "quote": self.claim["quote"].replace("15", "25")}
        self.assertEqual(check_reference(changed, self.pages), ("unverified", []))

    def test_normalized_whitespace(self):
        changed = {**self.claim, "quote": self.claim["quote"].replace("15 %", "15\u00a0%").upper()}
        self.assertEqual(check_reference(changed, self.pages), ("verified", [2]))

    def test_empty_quote(self):
        self.assertEqual(check_reference({**self.claim, "quote": "  "}, self.pages),
                         ("empty_quote", []))

    def test_duplicate_pages(self):
        with self.assertRaises(ValueError):
            build_index([self.case["pages"][0], self.case["pages"][0]])


if __name__ == "__main__":
    unittest.main()
