"""chunkcite: structure-aware chunking, citation verification, no-LLM retrieval eval."""

from .chunking import Chunk, chunk_text, chunk_file
from .verify import ClaimResult, verify_claims
from .retrieval import retrieve, evaluate_retrieval

__all__ = [
    "Chunk",
    "chunk_text",
    "chunk_file",
    "ClaimResult",
    "verify_claims",
    "retrieve",
    "evaluate_retrieval",
]
__version__ = "0.1.0"
