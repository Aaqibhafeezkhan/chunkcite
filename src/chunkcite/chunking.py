"""Structure-aware chunking.

Rules, in order:
1. Headings (``#`` .. ``######``) start a new section; the heading path is
   kept on every chunk that follows, so a chunk is never an orphan fragment.
2. Markdown tables (consecutive lines starting with ``|``) are kept whole
   in a single chunk -- a table split across two embeddings is worse than
   no table, because a model will invent relationships between orphan rows.
3. Otherwise, paragraphs are chunks. Long paragraphs are split only at
   sentence boundaries, never mid-sentence, up to ``max_chars``.
4. Every chunk gets a stable id: ``sha1(source + locator + text)[:12]``,
   plus a locator (file, line range, and page when known) so a citation
   can be traced back to an exact place in the source.

No LLM, no network, no embeddings are involved. This is the part of RAG
that should be deterministic.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    heading_path: list[str]
    start_line: int
    end_line: int
    page: int | None = None
    kind: str = "paragraph"  # paragraph | table | heading

    def to_dict(self) -> dict:
        return asdict(self)


def _stable_id(source: str, locator: str, text: str) -> str:
    h = hashlib.sha1(f"{source}\n{locator}\n{text}".encode()).hexdigest()
    return h[:12]


def _split_long_paragraph(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    sentences = _SENTENCE.split(text)
    parts, current = [], ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > max_chars and current:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    # A single pathological sentence longer than max_chars is kept whole
    # rather than split mid-sentence; splitting it would destroy the claim.
    return parts


def chunk_text(text: str, source: str, max_chars: int = 1200) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []
    heading_stack: list[tuple[int, str]] = []

    def heading_path() -> list[str]:
        return [title for _, title in heading_stack]

    i = 0
    while i < len(lines):
        line = lines[i]
        match = _HEADING.match(line)
        if match:
            level, title = len(match.group(1)), match.group(2)
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        # Tables: keep the whole block together.
        if line.lstrip().startswith("|"):
            start = i
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            table_text = "\n".join(block)
            locator = f"L{start + 1}-{i}"
            chunks.append(
                Chunk(
                    id=_stable_id(source, locator, table_text),
                    text=table_text,
                    source=source,
                    heading_path=heading_path(),
                    start_line=start + 1,
                    end_line=i,
                    kind="table",
                )
            )
            continue
        # Paragraph: consecutive non-blank, non-heading, non-table lines.
        start = i
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _HEADING.match(lines[i]) and not lines[i].lstrip().startswith("|"):
            para_lines.append(lines[i].strip())
            i += 1
        para = " ".join(para_lines)
        for part in _split_long_paragraph(para, max_chars):
            locator = f"L{start + 1}-{i}"
            chunks.append(
                Chunk(
                    id=_stable_id(source, locator, part),
                    text=part,
                    source=source,
                    heading_path=heading_path(),
                    start_line=start + 1,
                    end_line=i,
                    kind="paragraph",
                )
            )
    return chunks


def chunk_file(path: str | Path, max_chars: int = 1200) -> list[Chunk]:
    p = Path(path)
    source = p.name
    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "PDF support needs the pdf extra: pip install 'chunkcite[pdf]'"
            ) from exc
        chunks: list[Chunk] = []
        for page_no, page in enumerate(PdfReader(str(p)).pages, start=1):
            page_text = page.extract_text() or ""
            for chunk in chunk_text(page_text, source, max_chars=max_chars):
                chunk.page = page_no
                chunks.append(chunk)
        return chunks
    return chunk_text(p.read_text(encoding="utf-8"), source, max_chars=max_chars)


def audit(chunks: list[Chunk]) -> dict:
    """Cheap, deterministic chunk-quality audit for CI."""
    issues = []
    seen: dict[str, int] = {}
    for chunk in chunks:
        if not chunk.heading_path:
            issues.append(f"chunk {chunk.id}: no heading path (orphan)")
        if len(chunk.text) > 2000:
            issues.append(f"chunk {chunk.id}: over 2000 chars")
        if chunk.kind == "table" and chunk.text.count("\n") == 0:
            issues.append(f"chunk {chunk.id}: single-line table, may be truncated")
        seen[chunk.text] = seen.get(chunk.text, 0) + 1
    duplicates = sum(1 for v in seen.values() if v > 1)
    return {
        "chunks": len(chunks),
        "tables": sum(1 for c in chunks if c.kind == "table"),
        "orphans": sum(1 for c in chunks if not c.heading_path),
        "duplicate_texts": duplicates,
        "issues": issues,
    }
