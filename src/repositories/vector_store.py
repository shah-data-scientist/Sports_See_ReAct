"""
FILE: vector_store.py
STATUS: Active
RESPONSIBILITY: FAISS vector store data access layer for index CRUD operations
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Protocol

import faiss
import numpy as np

from src.core.config import settings
from src.core.exceptions import IndexNotFoundError, SearchError
from src.core.observability import logfire
from src.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers (dependency injection)."""

    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        ...


class VectorStoreRepository:
    """Repository for vector store operations.

    Handles FAISS index and document chunk storage with proper
    separation from business logic.

    Attributes:
        index: FAISS index for similarity search
        chunks: List of document chunks with metadata
    """

    def __init__(
        self,
        index_path: Path | None = None,
        chunks_path: Path | None = None,
    ):
        """Initialize repository.

        Args:
            index_path: Path to FAISS index file (default from settings)
            chunks_path: Path to chunks pickle file (default from settings)
        """
        self._index_path = index_path or settings.faiss_index_path
        self._chunks_path = chunks_path or settings.document_chunks_path
        self._index: faiss.Index | None = None
        self._chunks: list[DocumentChunk] = []
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Check if index is loaded."""
        return self._is_loaded and self._index is not None

    @property
    def index_size(self) -> int:
        """Get number of vectors in index."""
        if self._index is None:
            return 0
        return self._index.ntotal

    @property
    def chunks(self) -> list[DocumentChunk]:
        """Get document chunks (read-only copy)."""
        return self._chunks.copy()

    def load(self) -> bool:
        """Load index and chunks from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self._index_path.exists() or not self._chunks_path.exists():
            logger.warning(
                "Index files not found: %s, %s",
                self._index_path,
                self._chunks_path,
            )
            return False

        try:
            logger.info("Loading FAISS index from %s", self._index_path)
            self._index = faiss.read_index(str(self._index_path))

            logger.info("Loading chunks from %s", self._chunks_path)
            with open(self._chunks_path, "rb") as f:
                raw_chunks = pickle.load(f)

            # Convert to DocumentChunk models
            self._chunks = [
                DocumentChunk(
                    id=chunk.get("id", f"chunk_{i}"),
                    text=chunk.get("text", ""),
                    metadata=chunk.get("metadata", {}),
                )
                for i, chunk in enumerate(raw_chunks)
            ]

            self._is_loaded = True
            logger.info(
                "Loaded index with %d vectors and %d chunks",
                self._index.ntotal,
                len(self._chunks),
            )
            return True

        except Exception as e:
            logger.error("Failed to load index: %s", e)
            self._index = None
            self._chunks = []
            self._is_loaded = False
            return False

    def save(self) -> None:
        """Save index and chunks to disk.

        Raises:
            ValueError: If no index to save
        """
        if self._index is None:
            raise ValueError("No index to save")

        # Ensure directory exists
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._chunks_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Saving FAISS index to %s", self._index_path)
        faiss.write_index(self._index, str(self._index_path))

        logger.info("Saving %d chunks to %s", len(self._chunks), self._chunks_path)
        # Convert back to dict format for compatibility
        raw_chunks = [{"id": c.id, "text": c.text, "metadata": c.metadata} for c in self._chunks]
        with open(self._chunks_path, "wb") as f:
            pickle.dump(raw_chunks, f)

        logger.info("Index and chunks saved successfully")

    def build_index(
        self,
        chunks: list[DocumentChunk],
        embeddings: np.ndarray,
    ) -> None:
        """Build FAISS index from chunks and embeddings.

        Args:
            chunks: Document chunks to index
            embeddings: Embeddings array (n_chunks x embedding_dim)

        Raises:
            ValueError: If chunks and embeddings don't match
        """
        if len(chunks) != embeddings.shape[0]:
            raise ValueError(f"Mismatch: {len(chunks)} chunks but {embeddings.shape[0]} embeddings")

        # Normalize for cosine similarity
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)

        # Create index
        dimension = embeddings.shape[1]
        logger.info("Creating FAISS IndexFlatIP with dimension %d", dimension)
        self._index = faiss.IndexFlatIP(dimension)
        self._index.add(embeddings)

        self._chunks = chunks
        self._is_loaded = True

        logger.info("Built index with %d vectors", self._index.ntotal)

    @staticmethod
    def _compute_metadata_boost(chunk: DocumentChunk) -> float:
        """Compute additive score boost from Reddit metadata.

        With 1-comment-per-chunk, each chunk has exact per-comment metadata.

        Boost components (max total 5%):
        - Comment upvotes: 0-2% (relative ranking within same post)
          Lowest upvoted comment in post → 0%, highest → 2%
        - Post engagement: 0-1% (relative ranking across all 4 posts)
          Lowest upvoted post → 0%, highest → 1%
        - NBA official: +2.0 if is_nba_official == 1 → 0 or 2%
          (authoritative source)

        Non-Reddit chunks get 0.0 boost.

        Args:
            chunk: Document chunk with metadata

        Returns:
            Additive boost value (0.0 to 5.0)
        """
        if chunk.metadata.get("type") != "reddit_thread":
            return 0.0

        boost = 0.0

        # Comment upvotes boost (0-2%): relative within post
        comment_upvotes = chunk.metadata.get("comment_upvotes", 0)
        min_comment_upvotes = chunk.metadata.get("min_comment_upvotes_in_post", 0)
        max_comment_upvotes = chunk.metadata.get("max_comment_upvotes_in_post", 0)

        if isinstance(comment_upvotes, (int, float)) and max_comment_upvotes > min_comment_upvotes:
            # Linear gradation: 0% for lowest, 2% for highest
            ratio = (comment_upvotes - min_comment_upvotes) / (max_comment_upvotes - min_comment_upvotes)
            boost += 2.0 * ratio
        elif max_comment_upvotes == min_comment_upvotes and comment_upvotes > 0:
            # All comments have same upvotes → give middle value
            boost += 1.0

        # Post engagement boost (0-1%): relative across all posts
        post_upvotes = chunk.metadata.get("post_upvotes", 0)
        min_post_upvotes = chunk.metadata.get("min_post_upvotes_global", 0)
        max_post_upvotes = chunk.metadata.get("max_post_upvotes_global", 0)

        if isinstance(post_upvotes, (int, float)) and max_post_upvotes > min_post_upvotes:
            # Linear gradation: 0% for lowest post, 1% for highest post
            ratio = (post_upvotes - min_post_upvotes) / (max_post_upvotes - min_post_upvotes)
            boost += 1.0 * ratio
        elif max_post_upvotes == min_post_upvotes and post_upvotes > 0:
            # All posts have same upvotes → give middle value
            boost += 0.5

        # NBA official boost (0 or 2%)
        if chunk.metadata.get("is_nba_official") == 1:
            boost += 2.0

        return boost

    @staticmethod
    def _compute_quality_boost(chunk: DocumentChunk) -> float:
        """Compute additive score boost from chunk quality assessment.

        Maps the LLM-assessed quality_score (0.0-1.0) to a boost value
        on the same 0-5 scale as metadata boost.

        Args:
            chunk: Document chunk with quality_score in metadata.

        Returns:
            Additive boost value (0.0 to 5.0). Returns 0.0 if no score.
        """
        quality_score = chunk.metadata.get("quality_score")
        if quality_score is None:
            return 0.0
        return float(quality_score) * 5.0

    @logfire.instrument("VectorStoreRepository.search {k=}")
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        min_score: float | None = None,
        metadata_filters: dict[str, Any] | None = None,
        query_text: str | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for similar documents with BM25 reranking and metadata boosting.

        Phase 13 (Vector remediation): Implements 3-signal hybrid scoring
        - Cosine similarity (50%): Semantic match
        - BM25 (35%): Term-based relevance (requires query_text)
        - Metadata boost (15%): Authority signals (upvotes, NBA official)

        Args:
            query_embedding: Query embedding vector (1 x dim)
            k: Number of results to return
            min_score: Minimum similarity score (0-1)
            metadata_filters: Optional dict to filter chunks by metadata
            query_text: Optional original query text for BM25 reranking

        Returns:
            List of (chunk, score) tuples sorted by score descending

        Raises:
            IndexNotFoundError: If index not loaded
            SearchError: If search fails
        """
        if not self.is_loaded:
            raise IndexNotFoundError()

        try:
            # Normalize query
            query_embedding = query_embedding.astype("float32")
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding)

            # If metadata filters provided, pre-filter chunks
            if metadata_filters:
                filtered_indices = []
                for i, chunk in enumerate(self._chunks):
                    # Check if chunk metadata matches all filters
                    matches = all(
                        chunk.metadata.get(key) == value
                        for key, value in metadata_filters.items()
                    )
                    if matches:
                        filtered_indices.append(i)

                if not filtered_indices:
                    # No chunks match filters, fall back to unfiltered search
                    logger.warning(
                        f"No chunks matched metadata filters {metadata_filters}, using all chunks"
                    )
                    filtered_indices = list(range(len(self._chunks)))

                # Search within filtered subset
                # Create temporary index with filtered vectors
                filtered_vectors = np.array(
                    [self._index.reconstruct(i) for i in filtered_indices]
                )
                temp_index = faiss.IndexFlatIP(filtered_vectors.shape[1])
                temp_index.add(filtered_vectors)

                # Adaptive over-retrieval (smaller k = less over-retrieval needed)
                if k <= 3:
                    search_k = min(k * 2, len(filtered_indices))  # 2x for small k
                elif k <= 5:
                    search_k = min(int(k * 1.5), len(filtered_indices))  # 1.5x for medium k
                else:
                    search_k = min(int(k * 1.2), len(filtered_indices))  # 1.2x for large k
                scores, indices = temp_index.search(query_embedding, search_k)

                # Map back to original indices
                original_indices = [filtered_indices[idx] for idx in indices[0]]
                scores = scores[0]
            else:
                # Normal search without metadata filtering
                # Adaptive over-retrieval (smaller k = less over-retrieval needed)
                if k <= 3:
                    search_k = k * 2  # 2x for small k
                elif k <= 5:
                    search_k = int(k * 1.5)  # 1.5x for medium k
                else:
                    search_k = int(k * 1.2)  # 1.2x for large k
                scores, indices = self._index.search(query_embedding, search_k)
                original_indices = indices[0]
                scores = scores[0]

            results: list[tuple[DocumentChunk, float]] = []
            cosine_scores = []  # Track for BM25 normalization
            for i, idx in enumerate(original_indices):
                if idx < 0 or idx >= len(self._chunks):
                    continue

                # Convert score to percentage (0-100)
                score_percent = float(scores[i]) * 100

                # Apply minimum score filter
                if min_score is not None and score_percent < (min_score * 100):
                    continue

                results.append((self._chunks[idx], score_percent))
                cosine_scores.append(score_percent)

            # Phase 13: 3-Signal Hybrid Scoring (Cosine + BM25 + Metadata)
            if query_text and results:
                # Calculate BM25 scores
                try:
                    from rank_bm25 import BM25Okapi

                    # Extract text from candidates for BM25
                    chunk_texts = [chunk.text for chunk, _ in results]
                    query_tokens = query_text.lower().split()

                    # Build BM25 model
                    tokenized_chunks = [text.lower().split() for text in chunk_texts]
                    bm25 = BM25Okapi(tokenized_chunks)
                    bm25_scores = bm25.get_scores(query_tokens)

                    # Normalize BM25 to 0-100
                    if bm25_scores.max() > 0:
                        bm25_normalized = (bm25_scores / bm25_scores.max()) * 100
                    else:
                        bm25_normalized = bm25_scores

                    # Apply 3-signal formula: (cosine*0.70) + (bm25*0.15) + (quality*0.15)
                    # Quality boost = LLM-assessed quality score only (Option B: simplified)
                    new_results = []
                    for i, (chunk, cosine_score) in enumerate(results):
                        bm25_score = bm25_normalized[i]

                        # Quality-only boost (simplified from metadata+quality)
                        quality_boost = self._compute_quality_boost(chunk)

                        # 3-signal composite score (quality-only)
                        composite_score = (
                            (cosine_score * 0.70)
                            + (bm25_score * 0.15)
                            + (quality_boost * 0.15)  # Quality only (no metadata)
                        )
                        composite_score = min(composite_score, 100.0)

                        new_results.append((chunk, composite_score))

                    results = new_results

                except ImportError:
                    # BM25 not available, fall back to cosine + quality
                    logger.warning("rank-bm25 not available, using cosine + quality only")
                    results = [
                        (chunk, min(
                            score + self._compute_quality_boost(chunk),
                            100.0,
                        ))
                        for chunk, score in results
                    ]
                except ImportError:
                    # BM25 library not installed
                    logger.warning("BM25 library (rank-bm25) not installed, using cosine + quality only")
                    results = [
                        (chunk, min(
                            score + self._compute_quality_boost(chunk),
                            100.0,
                        ))
                        for chunk, score in results
                    ]
                except Exception as e:
                    # BM25 calculation error (not import related)
                    logger.error(f"BM25 calculation error: {e}", exc_info=True)
                    results = [
                        (chunk, min(
                            score + self._compute_quality_boost(chunk),
                            100.0,
                        ))
                        for chunk, score in results
                    ]
            else:
                # No query_text provided, fall back to cosine + quality boosting
                results = [
                    (chunk, min(
                        score + self._compute_quality_boost(chunk),
                        100.0,
                    ))
                    for chunk, score in results
                ]

            # Sort by final score descending and limit to k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:k]

        except Exception as e:
            logger.error("Search failed: %s", e)
            raise SearchError(f"Search failed: {e}") from e

    def clear(self) -> None:
        """Clear index and chunks from memory."""
        self._index = None
        self._chunks = []
        self._is_loaded = False
        logger.info("Index cleared from memory")

    def delete_files(self) -> None:
        """Delete index files from disk."""
        if self._index_path.exists():
            self._index_path.unlink()
            logger.info("Deleted %s", self._index_path)

        if self._chunks_path.exists():
            self._chunks_path.unlink()
            logger.info("Deleted %s", self._chunks_path)

        self.clear()
