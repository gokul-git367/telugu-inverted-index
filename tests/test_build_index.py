import sys
import unicodedata
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_index import build_index, clean_text, preprocess


class PreprocessingTests(unittest.TestCase):
    def test_cleans_entities_tags_and_whitespace(self):
        self.assertEqual(clean_text(" <p>తెలుగు&nbsp; భాష</p>\n రెండో వరుస "),
                         "తెలుగు భాష రెండో వరుస")

    def test_normalizes_equivalent_unicode(self):
        text = "తెలుగు"
        self.assertEqual(preprocess(text), preprocess(unicodedata.normalize("NFD", text)))

    def test_tokenizes_mixed_script_and_discards_punctuation(self):
        self.assertEqual(preprocess("తెలుగు, AI 2026!"), ["తెలుగు", "ai", "2026"])

    def test_handles_empty_input(self):
        self.assertEqual(preprocess(None), [])


class IndexTests(unittest.TestCase):
    def test_builds_frequency_postings_and_document_ids(self):
        index = build_index(
            [{"id": "17", "title": "తెలుగు భాష", "text": "తెలుగు భాష తెలుగు."}],
            {"భాష"}, "wikimedia/wikipedia", "CC BY-SA", "https://example.test",
            {"source_documents": 10, "method": "test sample"})
        self.assertEqual(index["postings"]["తెలుగు"], [["17", 3]])
        self.assertEqual(index["postings"]["భాష"], [["17", 2]])
        self.assertEqual(index["documents"][0]["title"], "తెలుగు భాష")
        self.assertEqual(index["metadata"]["documents"], 1)

    def test_preserves_benchmark_id_without_wikipedia_prefix(self):
        index = build_index([{"_id": "qrel-5", "text": "తెలుగు సమాచారం"}], set(),
                            "carlfeynman/Bharat_NanoMSMARCO_te", "CC-BY-4.0",
                            "https://example.test")
        self.assertEqual(index["postings"]["తెలుగు"], [["qrel-5", 1]])


if __name__ == "__main__":
    unittest.main()