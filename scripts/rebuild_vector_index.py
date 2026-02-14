"""
FILE: rebuild_vector_index.py
STATUS: Active
RESPONSIBILITY: Rebuild FAISS vector index with Reddit-aware chunking and per-PDF checkpointing
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import logging
import os
import pickle
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import DataPipeline
from src.pipeline.models import RawDocument

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Checkpoint paths
CACHE_DIR = Path("data/vector")
OCR_PER_FILE_DIR = CACHE_DIR / "_ocr_per_file"
CHUNK_CACHE = CACHE_DIR / "_chunk_cache.pkl"
EMBED_CACHE = CACHE_DIR / "_embed_cache.pkl"
# Legacy cache (cleared on fresh start)
OCR_CACHE_LEGACY = CACHE_DIR / "_ocr_cache.pkl"


def _load_pickle(path: Path) -> object | None:
    """Load a pickle cache file if it exists."""
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def _save_pickle(path: Path, data: object) -> None:
    """Save data to a pickle cache file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"  Checkpoint saved: {path} ({path.stat().st_size / 1024:.1f} KB)", flush=True)


def _clear_stale_caches() -> None:
    """Clear intermediate caches (chunk, embed) but preserve per-file OCR caches.

    Per-file OCR caches (~30 min of easyOCR work) are preserved as checkpoints.
    Only chunk and embed caches are cleared since they depend on chunking logic
    which may have changed.
    """
    stale = [OCR_CACHE_LEGACY, CHUNK_CACHE, EMBED_CACHE]
    for path in stale:
        if path.exists():
            path.unlink()
            print(f"  Cleared stale cache: {path}", flush=True)

    # Per-file OCR caches are intentionally preserved (expensive to regenerate)
    if OCR_PER_FILE_DIR.exists():
        cached_files = list(OCR_PER_FILE_DIR.glob("*.pkl"))
        if cached_files:
            print(f"  Preserving {len(cached_files)} per-file OCR caches (easyOCR checkpoints)", flush=True)


def _ocr_single_pdf(file_path: Path) -> str | None:
    """OCR a single PDF with per-file checkpointing.

    Returns:
        Extracted text, or None if extraction fails.
    """
    cache_file = OCR_PER_FILE_DIR / f"{file_path.stem}.pkl"

    # Check per-file cache
    if cache_file.exists():
        cached = _load_pickle(cache_file)
        if cached:
            print(f"  [CACHED] {file_path.name} ({len(cached)} chars)", flush=True)
            return cached

    # Do fresh OCR
    from src.utils.data_loader import extract_text_from_pdf_with_ocr

    print(f"  [OCR] {file_path.name} ...", end="", flush=True)
    text = extract_text_from_pdf_with_ocr(str(file_path))

    if text:
        print(f" {len(text)} chars", flush=True)
        # Save per-file checkpoint
        OCR_PER_FILE_DIR.mkdir(parents=True, exist_ok=True)
        _save_pickle(cache_file, text)
    else:
        print(f" EMPTY (no text extracted)", flush=True)

    return text


def _load_documents_with_checkpoints(input_dir: str) -> list[RawDocument]:
    """Load all documents with per-PDF OCR checkpointing.

    PDFs are OCR'd individually with per-file caching so a crash at PDF 3
    doesn't lose the work from PDFs 1 and 2.

    Non-PDF files (Excel, TXT, DOCX) are loaded normally (they're fast).
    """
    from src.utils.data_loader import (
        extract_text_from_csv,
        extract_text_from_docx,
        extract_text_from_excel,
        extract_text_from_pdf,
        extract_text_from_txt,
    )

    input_path = Path(input_dir)
    documents = []

    # Excluded Excel sheets (structured data already in SQL database)
    EXCLUDED_EXCEL_SHEETS = {"Données NBA", "Analyse"}

    for file_path in sorted(input_path.rglob("*.*")):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        relative = file_path.relative_to(input_path)

        extracted_content = None

        if ext == ".pdf":
            # Check if standard text extraction works (non-image PDFs)
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(file_path))
                std_text = "".join(
                    page.extract_text() + "\n"
                    for page in reader.pages
                    if page.extract_text()
                )
                if len(std_text.strip()) >= 100:
                    extracted_content = std_text
                    print(f"  [TEXT] {file_path.name} ({len(std_text)} chars)", flush=True)
                else:
                    # Image PDF — use OCR with per-file checkpoint
                    extracted_content = _ocr_single_pdf(file_path)
            except Exception:
                extracted_content = _ocr_single_pdf(file_path)

        elif ext == ".docx":
            extracted_content = extract_text_from_docx(str(file_path))
        elif ext == ".txt":
            extracted_content = extract_text_from_txt(str(file_path))
        elif ext == ".csv":
            extracted_content = extract_text_from_csv(str(file_path))
        elif ext in (".xlsx", ".xls"):
            extracted_content = extract_text_from_excel(str(file_path))
        else:
            continue

        if not extracted_content:
            print(f"  [SKIP] {file_path.name} (no content)", flush=True)
            continue

        # Handle multi-sheet Excel (dict of sheet_name → text)
        if isinstance(extracted_content, dict):
            for sheet_name, text in extracted_content.items():
                if sheet_name in EXCLUDED_EXCEL_SHEETS:
                    print(f"  [SKIP] {file_path.name} sheet '{sheet_name}' (in SQL)", flush=True)
                    continue
                if text and text.strip():
                    documents.append(RawDocument(
                        page_content=text,
                        metadata={
                            "source": f"{relative} (Sheet: {sheet_name})",
                            "filename": file_path.name,
                            "sheet": sheet_name,
                        },
                    ))
        else:
            documents.append(RawDocument(
                page_content=extracted_content,
                metadata={
                    "source": str(relative),
                    "filename": file_path.name,
                },
            ))

    return documents


def main():
    """Rebuild vector index with per-PDF checkpointing."""

    print("=" * 80, flush=True)
    print("REBUILDING VECTOR INDEX (with per-PDF checkpointing)", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    # Prevent FAISS/OpenMP DLL conflict crash on Windows
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    # Clear stale caches from previous OCR engine / regex version
    print("[0] Clearing stale caches...", flush=True)
    _clear_stale_caches()
    print(flush=True)

    pipeline = DataPipeline()

    # ── [1/4] Load documents (per-PDF OCR with checkpoints) ──
    print("[1/4] Loading documents from data/inputs/ ...", flush=True)
    documents = _load_documents_with_checkpoints("data/inputs")
    print(f"\nLoaded {len(documents)} documents total", flush=True)
    print(flush=True)

    # ── [2/4] Clean documents ────────────────────────────────
    print("[2/4] Cleaning documents...", flush=True)
    clean_output = pipeline.clean(documents)
    print(f"Cleaned {len(clean_output.documents)} documents", flush=True)
    print(flush=True)

    # ── [3/4] Chunk documents (Reddit-aware) ─────────────────
    cached_chunks = _load_pickle(CHUNK_CACHE)
    if cached_chunks is not None:
        print(f"[3/4] Loading chunks from cache ({len(cached_chunks)} chunks)...", flush=True)
        chunks = cached_chunks
    else:
        print("[3/4] Chunking documents (Reddit-aware)...", flush=True)
        chunk_output = pipeline.chunk(clean_output.documents)
        chunks = chunk_output.chunks
        print(f"Created {len(chunks)} chunks", flush=True)

        # Show chunk statistics
        reddit_chunks = [c for c in chunks if c.metadata.get("type") == "reddit_thread"]
        standard_chunks = [c for c in chunks if c.metadata.get("type") != "reddit_thread"]
        print(f"  - Reddit chunks: {len(reddit_chunks)}", flush=True)
        print(f"  - Standard chunks: {len(standard_chunks)}", flush=True)

        # Max chunk chars check (embedding safety)
        max_chars = max(len(c.text) for c in chunks) if chunks else 0
        print(f"  - Max chunk chars: {max_chars} (~{max_chars // 4} tokens)", flush=True)

        # Reddit per-source breakdown
        if reddit_chunks:
            sources = {}
            for c in reddit_chunks:
                src = c.metadata.get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1
            print("  Reddit chunk breakdown by source:", flush=True)
            for src, count in sorted(sources.items()):
                total_comments = next(
                    (c.metadata.get("num_comments", "?")
                     for c in reddit_chunks
                     if c.metadata.get("source") == src),
                    "?",
                )
                print(f"    {src}: {count} chunks ({total_comments} comments)", flush=True)

        # Save chunk checkpoint
        _save_pickle(CHUNK_CACHE, chunks)

    print(flush=True)

    # ── [4/4] Embed and index ────────────────────────────────
    print("[4/4] Generating embeddings and building FAISS index...", flush=True)

    chunk_texts = [chunk.text for chunk in chunks]
    embed_output, embeddings = pipeline.embed(chunk_texts)

    pipeline._vector_store.build_index(chunks, embeddings)
    pipeline._vector_store.save()

    print(f"FAISS index created with {len(chunks)} vectors", flush=True)
    print(flush=True)

    # ── Summary ──────────────────────────────────────────────
    reddit_chunks = [c for c in chunks if c.metadata.get("type") == "reddit_thread"]
    standard_chunks = [c for c in chunks if c.metadata.get("type") != "reddit_thread"]
    print("=" * 80, flush=True)
    print("SUCCESS - Vector index rebuilt!", flush=True)
    print("=" * 80, flush=True)
    print(f"Total chunks: {len(chunks)}", flush=True)
    print(f"  Reddit: {len(reddit_chunks)}", flush=True)
    print(f"  Standard: {len(standard_chunks)}", flush=True)
    print(f"Index location: data/vector/", flush=True)

    # Clean up intermediate caches on success (keep per-file OCR for future rebuilds)
    for cache_path in (CHUNK_CACHE, EMBED_CACHE):
        if cache_path.exists():
            cache_path.unlink()
            print(f"  Cleaned cache: {cache_path}", flush=True)


if __name__ == "__main__":
    # Force UTF-8 encoding for stdout
    if sys.stdout.encoding != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    main()
