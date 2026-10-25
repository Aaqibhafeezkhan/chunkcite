"""chunkcite CLI: chunk | verify | eval | audit. All offline, all deterministic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .chunking import audit, chunk_file
from .retrieval import evaluate_retrieval
from .verify import verify_claims


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _load_json(path: Path):
    return json.loads(path.read_text())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chunkcite")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("chunk", help="Chunk documents into JSONL with locators")
    p.add_argument("inputs", nargs="+", help="Markdown, text, or PDF files")
    p.add_argument("--out", default="-", help="Output JSONL file, or - for stdout")
    p.add_argument("--max-chars", type=int, default=1200)

    p = sub.add_parser("verify", help="Verify claims against cited chunks")
    p.add_argument("--chunks", required=True, help="JSONL produced by chunkcite chunk")
    p.add_argument("--claims", required=True, help="JSON file: list of {text, cite}")
    p.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Minimum token overlap required to support a paraphrase (default: 0.6)",
    )

    p = sub.add_parser("eval", help="Recall@k / MRR over a golden set, no LLM")
    p.add_argument("--chunks", required=True)
    p.add_argument("--golden", required=True, help="JSONL: {question, expected_chunk_ids}")
    p.add_argument("--k", type=int, default=5)

    p = sub.add_parser("audit", help="Chunk-quality audit for CI")
    p.add_argument("--chunks", required=True)

    args = parser.parse_args(argv)

    if args.command == "chunk":
        from .chunking import Chunk

        all_chunks: list[Chunk] = []
        for name in args.inputs:
            all_chunks.extend(chunk_file(name, max_chars=args.max_chars))
        text = "\n".join(json.dumps(c.to_dict()) for c in all_chunks)
        if args.out == "-":
            print(text)
        else:
            Path(args.out).write_text(text + "\n")
        print(f"{len(all_chunks)} chunks", file=sys.stderr)
        return 0

    chunks = None
    if args.command in {"verify", "eval", "audit"}:
        from .chunking import Chunk

        chunks = [Chunk(**row) for row in _load_jsonl(Path(args.chunks))]

    if args.command == "verify":
        claims = _load_json(Path(args.claims))
        results = [
            r.to_dict() for r in verify_claims(claims, chunks, threshold=args.threshold)
        ]
        print(json.dumps(results, indent=2))
        supported = sum(1 for r in results if r["verdict"] == "supported")
        print(f"{supported}/{len(results)} claims supported", file=sys.stderr)
        return 0 if supported == len(results) else 1

    if args.command == "eval":
        cases = _load_jsonl(Path(args.golden))
        print(json.dumps(evaluate_retrieval(cases, chunks, k=args.k), indent=2))
        return 0

    if args.command == "audit":
        report = audit(chunks)
        print(json.dumps(report, indent=2))
        return 0 if not report["issues"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
