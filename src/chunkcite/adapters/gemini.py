"""Optional Gemini / Vertex AI adapter — outside the offline core.

This module has no Google dependency and never reads an API key.
You supply ``generate_fn``: a callable taking a prompt string and
returning answer text. In production that callable wraps your own
Gemini or Vertex AI client (key from your environment, never committed).
In tests it is a fake that returns fixed text.

Flow:
1. ``build_prompt`` — question + numbered chunks, instructing the model
   to cite every claim as ``[chunk_id]``.
2. ``generate_fn(prompt)`` — your model call.
3. ``parse_claims`` — split the answer into sentences, keeping the
   ``[chunk_id]`` citation attached to each sentence.
4. ``verify_claims`` (core, offline) — each claim is checked against
   its cited chunk. An answer sentence without a citation is
   ``unresolved``, not silently passed.

If a sentence cites an unknown id, or its claim is not in the chunk,
verification flags it — the adapter never trusts the model.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from ..chunking import Chunk
from ..verify import ClaimResult, verify_claims

_CITE = re.compile(r"\[([0-9a-f]{12})\]")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    lines = [
        "Answer only from the chunks below. Cite every claim as [chunk_id].",
        "If the chunks do not contain the answer, say so and cite nothing.",
        "",
        f"Question: {question}",
        "",
        "Chunks:",
    ]
    for chunk in chunks:
        heading = " / ".join(chunk.heading_path) if chunk.heading_path else ""
        lines.append(f"[{chunk.id}] {heading}: {chunk.text}")
    return "\n".join(lines)


def parse_claims(answer_text: str) -> list[dict]:
    claims: list[dict] = []
    for sentence in _SENTENCE.split(answer_text.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        matches = _CITE.findall(sentence)
        clean = _CITE.sub("", sentence).strip()
        # A citation on its own after a period belongs to the previous
        # claim (e.g. "Claim. [abc123]" from a model that cites late).
        if not clean and matches and claims:
            claims[-1]["cite"] = matches[0]
            continue
        if not clean:
            continue
        claims.append({"text": clean, "cite": matches[0] if matches else None})
    return claims


def answer_and_verify(
    question: str,
    chunks: list[Chunk],
    generate_fn: Callable[[str], str],
    threshold: float = 0.6,
) -> dict:
    prompt = build_prompt(question, chunks)
    answer = generate_fn(prompt)
    claims = parse_claims(answer)
    results: list[ClaimResult] = verify_claims(claims, chunks, threshold=threshold)
    return {
        "prompt": prompt,
        "answer": answer,
        "claims": claims,
        "verification": [r.to_dict() for r in results],
        "supported": sum(1 for r in results if r.verdict == "supported"),
        "total": len(results),
    }
