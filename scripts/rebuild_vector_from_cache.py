"""
Rebuild vector store from cached OCR files (skip Excel, skip re-running OCR).

Uses cached Reddit PDF OCR results from data/vector/_ocr_per_file/
"""
import pickle
import logging
from pathlib import Path

from src.repositories.vector_store import VectorStoreRepository
from src.services.embedding import EmbeddingService
from src.models.document import DocumentChunk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.pipeline.reddit_chunker import RedditThreadChunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load cached OCR results
    cache_dir = Path("data/vector/_ocr_per_file")
    cached_files = list(cache_dir.glob("Reddit *.pkl"))

    logger.info(f"Found {len(cached_files)} cached OCR files")

    all_chunks = []

    for cache_file in sorted(cached_files):
        logger.info(f"Loading cached OCR: {cache_file.name}")

        # Load pickled OCR text
        with open(cache_file, 'rb') as f:
            ocr_text = pickle.load(f)

        logger.info(f"  Loaded {len(ocr_text)} characters")

        # Chunk using Reddit-aware chunker
        reddit_chunker = RedditThreadChunker()
        chunk_data_list = reddit_chunker.chunk_reddit_thread(
            text=ocr_text,
            source=cache_file.stem + ".pdf"
        )

        # Convert ChunkData to DocumentChunk
        chunks = [
            DocumentChunk(
                id=f"{cache_file.stem}_{idx}",
                text=chunk.text,
                metadata=chunk.metadata
            )
            for idx, chunk in enumerate(chunk_data_list)
        ]

        logger.info(f"  Created {len(chunks)} chunks")
        all_chunks.extend(chunks)

    logger.info(f"Total chunks: {len(all_chunks)}")

    # Build vector store
    logger.info("Initializing embedding service and vector store...")
    embedding_service = EmbeddingService()
    vector_store = VectorStoreRepository()

    logger.info("Generating embeddings...")
    embeddings = embedding_service.embed_batch([c.text for c in all_chunks])

    logger.info("Building FAISS index...")
    vector_store.build_index(chunks=all_chunks, embeddings=embeddings)

    logger.info("Saving index to disk...")
    vector_store.save()

    logger.info("✅ Vector store rebuilt successfully!")
    logger.info(f"   Sources: {len(cached_files)} Reddit PDFs (Excel excluded)")
    logger.info(f"   Total chunks: {len(all_chunks)}")
    logger.info(f"   Index saved to: {vector_store.index_path}")

if __name__ == "__main__":
    main()
