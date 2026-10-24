import unittest

from chunkcite.chunking import chunk_text
from chunkcite.retrieval import evaluate_retrieval, retrieve


DOC = """# Vector search

## pgvector

pgvector adds vector similarity search to Postgres with HNSW and IVFFlat indexes.

## Gemini

Gemini models accept long context windows and multimodal inputs.
"""


class TestRetrieval(unittest.TestCase):
    def test_retrieval_finds_pgvector_chunk(self):
        chunks = chunk_text(DOC, "doc.md")
        top = retrieve("pgvector HNSW index", chunks, k=1)
        self.assertEqual(len(top), 1)
        self.assertIn("pgvector", top[0].text)

    def test_eval_recall(self):
        chunks = chunk_text(DOC, "doc.md")
        target = [c for c in chunks if "pgvector" in c.text][0]
        report = evaluate_retrieval(
            [{"question": "What does pgvector add to Postgres?",
              "expected_chunk_ids": [target.id]}],
            chunks,
            k=5,
        )
        self.assertEqual(report["recall@5"], 1.0)
        self.assertEqual(report["cases"], 1)


if __name__ == "__main__":
    unittest.main()
