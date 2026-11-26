import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ask import check_answer, quote_from_yandex, retrieve


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.pages = json.loads(Path(__file__).with_name("example.json").read_text(encoding="utf-8"))["pages"]

    def test_retrieves_only_relevant_page(self):
        self.assertEqual(retrieve("Какой аванс предусмотрен?", self.pages), [self.pages[0]])

    def test_no_overlap(self):
        self.assertEqual(retrieve("Погода завтра?", self.pages), [])

    def test_answer_must_cite_retrieved_context(self):
        claim = {"document": "Условия договора", "page": 3, "quote": self.pages[1]["text"]}
        context = retrieve("Какой аванс предусмотрен?", self.pages)
        self.assertEqual(check_answer(claim, context)["status"], "unverified")

    def test_empty_and_malformed_responses(self):
        self.assertEqual(check_answer({}, self.pages), {"status": "no_answer"})
        with self.assertRaises(ValueError):
            check_answer({"document": "График работ", "page": False, "quote": []}, self.pages)

    def test_provider_contract_offline(self):
        expected = {"document": "Условия договора", "page": 2, "quote": self.pages[0]["text"]}
        response = {"result": {"alternatives": [{"message": {"text": json.dumps(expected)}}]}}
        with patch("ask.urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as transport:
            answer = quote_from_yandex("Какой аванс?", self.pages[:1], "test-key", "gpt://test/model")
        body = json.loads(transport.call_args.args[0].data)
        self.assertEqual(json.loads(body["messages"][-1]["text"])["pages"], self.pages[:1])
        self.assertEqual(check_answer(answer, self.pages[:1])["status"], "verified")


if __name__ == "__main__":
    unittest.main()
