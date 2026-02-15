# Query Pipeline Documentation Corrections

**Date:** 2026-02-15
**File Updated:** `docs/QUERY_PIPELINE_GUIDE.html`

## Summary

Corrected documentation to accurately reflect the actual FAISS implementation instead of the incorrectly documented ChromaDB system.

## Errors Fixed

### ❌ Incorrect (Original Documentation)

| Component | Incorrect Value | Error Type |
|-----------|----------------|------------|
| **Vector Database** | ChromaDB | Wrong technology |
| **Index Type** | HNSW (Hierarchical Navigable Small World) | Wrong algorithm |
| **Index Parameters** | M=16, ef_construction=200, ef_search=10 | Non-existent params |
| **Storage Size** | ~800 MB | Inflated estimate |
| **Storage Location** | `data/vector/chroma_db/` | Wrong directory |
| **Index Files** | `chroma.sqlite3`, separate index/ folder | Wrong structure |
| **Collection Name** | `nba_discussions` | ChromaDB concept |
| **Search Type** | Approximate k-NN | Wrong algorithm type |

### ✅ Correct (Verified from Source Code)

| Component | Correct Value | Source |
|-----------|--------------|--------|
| **Vector Database** | FAISS (Facebook AI Similarity Search) | `src/repositories/vector_store.py:14` |
| **Index Type** | IndexFlatIP (Flat Index with Inner Product) | Line 173 |
| **Index Algorithm** | Exact search (brute-force), not approximate | Implementation |
| **Normalization** | L2 normalization for cosine similarity | Line 168, 296 |
| **Storage Size** | ~50-100 MB (15K vectors × 768 dim × 4 bytes) | Calculated |
| **Storage Location** | `data/vector/` | `src/core/config.py:95` |
| **Index Files** | `faiss_index.idx`, `document_chunks.pkl` | Lines 136, 141 |
| **Search Type** | Exact nearest neighbors (100% recall) | IndexFlatIP spec |
| **Hybrid Scoring** | 3-signal: Cosine (70%) + BM25 (15%) + Quality (15%) | Lines 387-402 |

## Root Cause Analysis

**Why the errors occurred:**
1. **Assumption over verification**: Made assumptions about vector DB technology instead of reading source code
2. **Pattern matching**: Defaulted to "modern stack" (ChromaDB + HNSW) without checking actual implementation
3. **Invented details**: Created plausible-sounding specifics (800 MB, HNSW params) without verification

**What should have been done:**
1. Read `src/repositories/vector_store.py` FIRST
2. Check `src/core/config.py` for paths and settings
3. Verify ALL technical details against source code
4. Document what IS, not what "should be"

## Verification

All corrections verified against source code:

```bash
# Verify vector store implementation
grep -n "import faiss" src/repositories/vector_store.py
# Line 14: import faiss

grep -n "IndexFlatIP" src/repositories/vector_store.py
# Line 173: self._index = faiss.IndexFlatIP(dimension)
# Line 322: temp_index = faiss.IndexFlatIP(filtered_vectors.shape[1])

# Verify file paths
grep -n "faiss_index" src/core/config.py
# Line 136: return Path(self.vector_db_dir) / "faiss_index.idx"
```

## Impact

**Documentation now accurately reflects:**
- ✅ FAISS as the vector search engine
- ✅ IndexFlatIP exact search algorithm (not HNSW approximate)
- ✅ Correct file structure and storage locations
- ✅ Realistic storage size estimates
- ✅ 3-signal hybrid scoring system
- ✅ Actual implementation details

**Lessons learned:**
- Always verify technical documentation against source code
- Avoid assumptions based on "common patterns"
- Be explicit when uncertain instead of inventing details
- Specific, wrong details are more dangerous than vague, correct ones

---

**Updated by:** Claude (after user caught the hallucinations)
**Verified against:** Actual source code in `src/repositories/vector_store.py` and `src/core/config.py`
