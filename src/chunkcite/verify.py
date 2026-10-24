"""Citation verification without an LLM judge.

A claim is SUPPORTED only if the cited chunk actually contains it:
- exact normalised substring match, or
- token overlap >= ``threshold`` on the claim's content words
  (stopwords removed), so paraphrase is tolerated but invention is not.

Anything else is UNSUPPORTED, and a claim citing an unknown chunk id
is UNRESOLVED. No model is asked to judge its own output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .chunking import Chunk

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "to", "in", "on", "for", "with", "and", "or", "by", "at", "as",
    "it", "its", "this", "that", "these", "those", "from", "into",
}
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


@dataclass
class ClaimResult:
    claim: str
    chunk_id: str | None
    verdict: str  # supported | unsupported | unresolved
    overlap: float
    excerpt: str = ""

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "chunk_id": self.chunk_id,
            "verdict": self.verdict,
            "overlap": round(self.overlap, 3),
            "excerpt": self.excerpt,
        }


def verify_claims(
    claims: list[dict], chunks: list[Chunk], threshold: float = 0.6
) -> list[ClaimResult]:
    by_id = {c.id: c for c in chunks}
    results: list[ClaimResult] = []
    for claim in claims:
        text = claim.get("text", "")
        chunk_id = claim.get("cite")
        chunk = by_id.get(chunk_id) if chunk_id else None
        if chunk is None:
            results.append(ClaimResult(text, chunk_id, "unresolved", 0.0))
            continue
        if _normalise(text) and _normalise(text) in _normalise(chunk.text):
            results.append(
                ClaimResult(text, chunk_id, "supported", 1.0, chunk.text[:200])
            )
            continue
        claim_tokens, chunk_tokens = _tokens(text), _tokens(chunk.text)
        overlap = (
            len(claim_tokens & chunk_tokens) / len(claim_tokens)
            if claim_tokens
            else 0.0
        )
        verdict = "supported" if overlap >= threshold else "unsupported"
        results.append(
            ClaimResult(text, chunk_id, verdict, overlap, chunk.text[:200])
        )
    return results
