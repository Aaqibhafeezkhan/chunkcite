import unittest

from chunkcite.chunking import audit, chunk_text


DOC = """# Retrieval

## Chunking

Split documents at headings, never mid-sentence.

| model | recall |
|---|---|
| A | 0.9 |
| B | 0.8 |

## Citations

Every chunk keeps its heading path and line range.
"""


class TestChunking(unittest.TestCase):
    def test_table_kept_whole(self):
        chunks = chunk_text(DOC, "doc.md")
        tables = [c for c in chunks if c.kind == "table"]
        self.assertEqual(len(tables), 1)
        self.assertIn("| A | 0.9 |", tables[0].text)

    def test_heading_path_preserved(self):
        chunks = chunk_text(DOC, "doc.md")
        cite = [c for c in chunks if "heading path" in c.text][0]
        self.assertEqual(cite.heading_path, ["Retrieval", "Citations"])

    def test_ids_stable(self):
        self.assertEqual(
            [c.id for c in chunk_text(DOC, "doc.md")],
            [c.id for c in chunk_text(DOC, "doc.md")],
        )

    def test_long_paragraph_splits_at_sentences(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(100))
        chunks = chunk_text(text, "doc.md", max_chars=200)
        self.assertTrue(all(len(c.text) <= 250 for c in chunks))
        self.assertTrue(all(c.text.endswith(".") for c in chunks))

    def test_audit_flags_orphan(self):
        chunks = chunk_text("No heading at all here.", "doc.md")
        self.assertEqual(audit(chunks)["orphans"], 1)


if __name__ == "__main__":
    unittest.main()
