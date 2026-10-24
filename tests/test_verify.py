import unittest

from chunkcite.chunking import chunk_text
from chunkcite.verify import verify_claims


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.chunks = chunk_text(
            "# Facts\n\nThe pgvector index uses HNSW by default.\n", "doc.md"
        )
        self.cid = self.chunks[0].id

    def test_exact_match_supported(self):
        (result,) = verify_claims(
            [{"text": "The pgvector index uses HNSW by default.", "cite": self.cid}],
            self.chunks,
        )
        self.assertEqual(result.verdict, "supported")

    def test_invented_number_unsupported(self):
        (result,) = verify_claims(
            [{"text": "The pgvector index uses HNSW and is 99 percent faster.", "cite": self.cid}],
            self.chunks,
        )
        self.assertEqual(result.verdict, "unsupported")

    def test_unknown_chunk_unresolved(self):
        (result,) = verify_claims(
            [{"text": "Anything.", "cite": "deadbeef0000"}], self.chunks
        )
        self.assertEqual(result.verdict, "unresolved")


if __name__ == "__main__":
    unittest.main()
