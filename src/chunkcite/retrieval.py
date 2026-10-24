"""Deterministic, no-LLM retrieval eval.

Scorer: plain BM25-style term frequency over chunk text, implemented in
the standard library. No embeddings, no API key, no judge model -- so the
numbers in the README are reproducible on any machine, and a regression
in chunking shows up as a regression in recall@k, not as a vibe.

Metrics: recall@k (share of expected chunks in the top-k) and MRR
(mean reciprocal rank of the first expected chunk).
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .chunking import Chunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def retrieve(query: str, chunks: list[Chunk], k: int = 5) -> list[Chunk]:
    query_tokens = _tokens(query)
    if not query_tokens or not chunks:
        return []
    doc_freq: Counter[str] = Counter()
    docs: list[Counter[str]] = []
    for chunk in chunks:
        counts = Counter(_tokens(chunk.text))
        docs.append(counts)
        for token in counts:
            doc_freq[token] += 1
    n = len(chunks)
    scored: list[tuple[float, Chunk]] = []
    for counts, chunk in zip(docs, chunks):
        score = 0.0
        for token in query_tokens:
            if token not in counts:
                continue
            idf = math.log(1 + (n - doc_freq[token] + 0.5) / (doc_freq[token] + 0.5))
            score += counts[token] * idf
        # Small bonus for heading-path matches: a question naming a
        # section should find that section, not just a body mention.
        heading = " ".join(chunk.heading_path).lower()
        if any(token in heading for token in query_tokens):
            score += 1.0
        scored.append((score, chunk))
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return [chunk for score, chunk in scored[:k] if score > 0]


def evaluate_retrieval(
    cases: list[dict], chunks: list[Chunk], k: int = 5
) -> dict:
    recalls, reciprocal_ranks = [], []
    for case in cases:
        expected = set(case.get("expected_chunk_ids", []))
        if not expected:
            continue
        ranked = retrieve(case.get("question", ""), chunks, k=k)
        ranked_ids = [c.id for c in ranked]
        recalls.append(len(expected & set(ranked_ids)) / len(expected))
        rank = next(
            (i + 1 for i, cid in enumerate(ranked_ids) if cid in expected), None
        )
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
    n = len(recalls)
    return {
        "cases": n,
        "k": k,
        f"recall@{k}": round(sum(recalls) / n, 4) if n else 0.0,
        "mrr": round(sum(reciprocal_ranks) / n, 4) if n else 0.0,
    }
