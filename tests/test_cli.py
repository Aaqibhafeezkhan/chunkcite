import json
import tempfile
import unittest
from pathlib import Path

from chunkcite.chunking import chunk_text
from chunkcite.cli import main


class TestVerifyThresholdCLI(unittest.TestCase):
    def test_threshold_changes_borderline_paraphrase_verdict(self):
        chunks = chunk_text(
            "# Facts\n\nThe database stores vectors and supports semantic search.\n",
            "facts.md",
        )
        claim = {
            "text": "The database stores vectors and enables semantic search.",
            "cite": chunks[0].id,
        }

        with tempfile.TemporaryDirectory() as tmp:
            chunks_path = Path(tmp) / "chunks.jsonl"
            claims_path = Path(tmp) / "claims.json"
            chunks_path.write_text(
                "\n".join(json.dumps(chunk.to_dict()) for chunk in chunks) + "\n"
            )
            claims_path.write_text(json.dumps([claim]))

            default_result = main([
                "verify", "--chunks", str(chunks_path), "--claims", str(claims_path)
            ])
            strict_result = main([
                "verify", "--chunks", str(chunks_path), "--claims", str(claims_path),
                "--threshold", "0.9",
            ])

        self.assertEqual(default_result, 0)
        self.assertEqual(strict_result, 1)


if __name__ == "__main__":
    unittest.main()
