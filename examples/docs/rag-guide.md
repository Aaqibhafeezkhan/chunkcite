# A short, synthetic RAG guide

## Chunking

Split documents at headings, never mid-sentence. A chunk that starts
mid-clause loses the condition that changes the answer.

## Tables

Tables must stay whole. A table split across two embeddings lets a
model invent relationships between orphan rows.

| retriever | strength |
|---|---|
| BM25 | exact terms, dates, names |
| vector search | paraphrase and meaning |
| hybrid | both, with a reranker |

## Citations

Every chunk keeps its heading path and line range, so a citation can
be traced back to an exact place in the source document.

## pgvector

pgvector adds vector similarity search to Postgres with HNSW and
IVFFlat indexes. Switching embedding models requires re-embedding:
vectors from two different models are not comparable.
