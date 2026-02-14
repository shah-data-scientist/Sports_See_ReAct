"""
FILE: filter_vector_store.py
STATUS: Active
RESPONSIBILITY: Remove structured data chunks from vector store, keep only semantic content
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import pickle
import sys
from pathlib import Path

import faiss
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Sources to REMOVE (structured data already in SQL, or empty templates)
REMOVE_SOURCES = {
    "regular NBA.xlsx (Feuille: Données NBA)",   # Player stats -> nba_stats.db
    "regular NBA.xlsx (Feuille: Equipe)",         # Team lookup -> nba_stats.db
    "regular NBA.xlsx (Feuille: Analyse)",        # Empty template
}

# Dictionary source to REPLACE with better-formatted glossary
DICT_SOURCE = "regular NBA.xlsx (Feuille: Dictionnaire des données)"
DICT_VECTORIZED_PATH = project_root / "data" / "reference" / "nba_dictionary_vectorized.txt"

CHUNKS_PATH = project_root / "data" / "vector" / "document_chunks.pkl"
INDEX_PATH = project_root / "data" / "vector" / "faiss_index.idx"


def main():
    """Filter vector store: remove structured data, improve dictionary format."""
    # Force UTF-8 output
    if sys.stdout.encoding != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 60)
    print("FILTERING VECTOR STORE")
    print("=" * 60)

    # 1. Load existing chunks
    print("\n[1/4] Loading existing chunks...")
    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)
    print(f"  Loaded {len(chunks)} chunks")

    # 2. Filter and replace
    print("\n[2/4] Filtering chunks...")
    kept = []
    removed_count = 0
    dict_replaced = 0

    for c in chunks:
        src = c["metadata"].get("source", "")

        # Remove structured data and empty sheets
        if src in REMOVE_SOURCES:
            removed_count += 1
            continue

        # Replace dictionary with better format
        if src == DICT_SOURCE:
            if DICT_VECTORIZED_PATH.exists():
                with open(DICT_VECTORIZED_PATH, "r", encoding="utf-8") as f:
                    c["text"] = f.read()
                dict_replaced += 1

        kept.append(c)

    # Deduplicate: dictionary chunks become identical after replacement
    seen_texts = set()
    deduped = []
    dupes_removed = 0
    for c in kept:
        if c["text"] in seen_texts:
            dupes_removed += 1
            continue
        seen_texts.add(c["text"])
        deduped.append(c)
    kept = deduped

    print(f"  Removed: {removed_count} chunks (structured data / empty)")
    print(f"  Deduplicated: {dupes_removed} chunks (identical dictionary entries)")
    print(f"  Dictionary improved: {dict_replaced} chunks")
    print(f"  Kept: {len(kept)} chunks")

    for c in kept:
        src = c["metadata"].get("source", "")
        print(f"    -> {src} ({len(c['text']):,} chars)")

    # 3. Re-embed kept chunks
    print(f"\n[3/4] Embedding {len(kept)} chunks with Mistral...")
    from src.services.embedding import EmbeddingService

    embed_svc = EmbeddingService()
    texts = [c["text"] for c in kept]
    embeddings = embed_svc.embed_batch(texts)
    print(f"  Embeddings shape: {embeddings.shape}")

    # 4. Build and save FAISS index
    print("\n[4/4] Building FAISS index...")
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(kept, f)

    print(f"  FAISS index: {index.ntotal} vectors")

    print("\n" + "=" * 60)
    print(f"DONE: {len(chunks)} -> {len(kept)} chunks ({removed_count} removed)")
    print("=" * 60)


if __name__ == "__main__":
    main()
