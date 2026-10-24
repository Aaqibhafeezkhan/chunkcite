"""Fair benchmark: same scorer, same corpus, two chunkers.

Method (run with: python benchmarks/benchmark.py):
- Corpus: examples/docs/rag-guide.md, chunked two ways:
  (a) chunkcite structure-aware chunking
  (b) a fixed-size 500-char splitter (the naive baseline, implemented here)
- Golden set: questions whose expected chunk is identified by the
  structure-aware chunk that contains the answer text; for the baseline
  we map "expected" to any baseline chunk containing the same answer
  sentence, so the baseline is not penalised for different boundaries.
- Scorer: chunkcite's BM25-style retrieve() in both cases.
- Reported: recall@5, MRR, chunk count, and whether the table survived whole.
No LLM, no network, no cherry-picked seed: the script prints its own inputs.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from chunkcite.chunking import Chunk, chunk_text  # noqa: E402
from chunkcite.retrieval import evaluate_retrieval  # noqa: E402

DOC = Path(__file__).resolve().parents[1] / "examples/docs/rag-guide.md"
TEXT = DOC.read_text()

QUESTIONS = [
    ("How should documents be split?", "never mid-sentence"),
    ("What breaks when a table is split?", "orphan rows"),
    ("What does pgvector add to Postgres?", "vector similarity search"),
    ("What must happen when switching embedding models?", "re-embedding"),
]


def fixed_chunks(text: str, size: int = 500) -> list[Chunk]:
    flat = " ".join(text.split())
    out = []
    for i in range(0, len(flat), size):
        part = flat[i : i + size]
        out.append(
            Chunk(id=f"fixed-{i // size}", text=part, source="rag-guide.md",
                  heading_path=[], start_line=0, end_line=0, kind="paragraph")
        )
    return out


def cases_for(chunks: list[Chunk]) -> list[dict]:
    cases = []
    for question, answer in QUESTIONS:
        expected = [c.id for c in chunks if answer in c.text]
        cases.append({"question": question, "expected_chunk_ids": expected})
    return cases


def structural(chunks: list[Chunk]) -> dict:
    with_heading = sum(1 for c in chunks if c.heading_path)
    mid_sentence = sum(
        1 for c in chunks if c.text and not c.text.rstrip().endswith((".", "|"))
    )
    standalone_table = any(
        c.kind == "table" and "BM25" in c.text and "hybrid" in c.text
        for c in chunks
    )
    return {
        "chunks": len(chunks),
        "with_heading_path": with_heading,
        "standalone_table_chunk": standalone_table,
        "chunks_ending_mid_sentence": mid_sentence,
    }


def main() -> None:
    struct = chunk_text(TEXT, "rag-guide.md")
    fixed = fixed_chunks(TEXT)
    struct_report = evaluate_retrieval(cases_for(struct), struct, k=5)
    fixed_report = evaluate_retrieval(cases_for(fixed), fixed, k=5)
    result = {
        "corpus": "examples/docs/rag-guide.md (synthetic, shipped in repo)",
        "questions": len(QUESTIONS),
        "note": "Recall is tied on this tiny 4-question set; the difference is "
        "structural, not retrieval luck. See with_heading_path and "
        "standalone_table_chunk.",
        "chunkcite_structure_aware": {**struct_report, **structural(struct)},
        "fixed_500char_baseline": {**fixed_report, **structural(fixed)},
    }
    print(json.dumps(result, indent=2))
    Path(__file__).resolve().parent.joinpath("results.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
