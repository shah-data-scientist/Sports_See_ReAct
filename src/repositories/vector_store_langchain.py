"""
FILE: vector_store_langchain.py
STATUS: Active
RESPONSIBILITY: LangChain-compatible VectorStore wrapper for custom FAISS implementation
LAST MAJOR UPDATE: 2026-02-14 (Created for LangChain integration)
MAINTAINER: Shahu
"""

import logging
from typing import Any, Callable, Iterable, List, Optional, Tuple

import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

from src.models.document import DocumentChunk
from src.repositories.vector_store import VectorStoreRepository

logger = logging.getLogger(__name__)


class NBAVectorStore(VectorStore):
    """LangChain-compatible vector store wrapper for custom FAISS implementation.

    This wraps the existing VectorStoreRepository (which has sophisticated
    hybrid scoring) to provide a standard LangChain VectorStore interface.

    Features preserved from custom implementation:
    - 4-signal hybrid scoring (Cosine + BM25 + Metadata + Quality)
    - Reddit metadata boosting (upvotes, NBA official)
    - Quality score boosting
    - Metadata filtering
    """

    def __init__(
        self,
        embedding_function: Embeddings,
        vector_store_repo: Optional[VectorStoreRepository] = None,
    ):
        """Initialize LangChain-compatible vector store.

        Args:
            embedding_function: LangChain Embeddings instance
            vector_store_repo: Existing vector store repository (or creates new one)
        """
        self.embedding_function = embedding_function
        self._vector_store = vector_store_repo or VectorStoreRepository()

        # Load index if not already loaded
        if not self._vector_store.is_loaded:
            self._vector_store.load()

        logger.info(
            f"NBAVectorStore initialized with {self._vector_store.index_size} vectors"
        )

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add texts to vector store.

        Args:
            texts: Texts to add
            metadatas: Optional metadata for each text
            **kwargs: Additional arguments

        Returns:
            List of IDs for added texts
        """
        texts_list = list(texts)

        # Generate embeddings using LangChain embedding function
        embeddings = self.embedding_function.embed_documents(texts_list)
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # Create DocumentChunks
        chunks = []
        ids = []
        for i, text in enumerate(texts_list):
            chunk_id = f"chunk_{i}_{hash(text)}"
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            chunks.append(DocumentChunk(
                id=chunk_id,
                text=text,
                metadata=metadata
            ))
            ids.append(chunk_id)

        # Build index (this will replace existing index)
        self._vector_store.build_index(chunks, embeddings_array)

        logger.info(f"Added {len(texts_list)} texts to vector store")
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        **kwargs: Any,
    ) -> List[Document]:
        """Search for similar documents.

        Args:
            query: Query text
            k: Number of results
            **kwargs: Additional arguments (min_score, metadata_filters)

        Returns:
            List of similar documents
        """
        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)
        query_embedding_array = np.array(query_embedding, dtype=np.float32)

        # Extract optional parameters
        min_score = kwargs.get("min_score")
        metadata_filters = kwargs.get("metadata_filters")

        # Search using custom hybrid scoring
        results = self._vector_store.search(
            query_embedding=query_embedding_array,
            k=k,
            min_score=min_score,
            metadata_filters=metadata_filters,
            query_text=query,  # Enable BM25 reranking
        )

        # Convert to LangChain Documents
        documents = []
        for chunk, score in results:
            # Add score to metadata
            metadata = chunk.metadata.copy()
            metadata["score"] = score

            documents.append(Document(
                page_content=chunk.text,
                metadata=metadata
            ))

        return documents

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with scores.

        Args:
            query: Query text
            k: Number of results
            **kwargs: Additional arguments

        Returns:
            List of (document, score) tuples
        """
        # Generate query embedding
        query_embedding = self.embedding_function.embed_query(query)
        query_embedding_array = np.array(query_embedding, dtype=np.float32)

        # Extract optional parameters
        min_score = kwargs.get("min_score")
        metadata_filters = kwargs.get("metadata_filters")

        # Search using custom hybrid scoring
        results = self._vector_store.search(
            query_embedding=query_embedding_array,
            k=k,
            min_score=min_score,
            metadata_filters=metadata_filters,
            query_text=query,
        )

        # Convert to LangChain Documents with scores
        documents_with_scores = []
        for chunk, score in results:
            metadata = chunk.metadata.copy()

            documents_with_scores.append((
                Document(
                    page_content=chunk.text,
                    metadata=metadata
                ),
                score / 100.0  # Normalize to 0-1 scale for LangChain
            ))

        return documents_with_scores

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> "NBAVectorStore":
        """Create vector store from texts.

        Args:
            texts: Texts to add
            embedding: Embedding function
            metadatas: Optional metadata
            **kwargs: Additional arguments

        Returns:
            New NBAVectorStore instance
        """
        vector_store = cls(embedding_function=embedding)
        vector_store.add_texts(texts, metadatas=metadatas)
        return vector_store

    def as_retriever(self, **kwargs: Any) -> "NBARetriever":
        """Convert to LangChain retriever.

        Args:
            **kwargs: Retriever configuration (search_kwargs)

        Returns:
            NBARetriever instance
        """
        return NBARetriever(
            vectorstore=self,
            **kwargs
        )

    @staticmethod
    def _select_relevance_score_fn(score: float) -> float:
        """Normalize score to 0-1 range.

        Our custom scoring is 0-100, LangChain expects 0-1.

        Args:
            score: Score from vector store (0-100)

        Returns:
            Normalized score (0-1)
        """
        return score / 100.0


class NBARetriever(BaseRetriever):
    """LangChain-compatible retriever for NBA vector store.

    Provides standard retriever interface with advanced features:
    - Hybrid scoring (Cosine + BM25 + Metadata + Quality)
    - Minimum score thresholds
    - Metadata filtering
    """

    vectorstore: NBAVectorStore
    """NBA vector store instance."""

    search_kwargs: dict = {}
    """Search keyword arguments (k, min_score, metadata_filters)."""

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[Any] = None,
    ) -> List[Document]:
        """Get relevant documents for query.

        Args:
            query: Query text
            run_manager: Optional callback manager

        Returns:
            List of relevant documents
        """
        k = self.search_kwargs.get("k", 5)
        min_score = self.search_kwargs.get("min_score")
        metadata_filters = self.search_kwargs.get("metadata_filters")

        # Use vectorstore's similarity search
        documents = self.vectorstore.similarity_search(
            query=query,
            k=k,
            min_score=min_score,
            metadata_filters=metadata_filters,
        )

        return documents


def create_nba_retriever(
    embedding_function: Embeddings,
    vector_store_repo: Optional[VectorStoreRepository] = None,
    search_type: str = "similarity",
    search_kwargs: Optional[dict] = None,
) -> NBARetriever:
    """Factory function to create NBA retriever with LangChain compatibility.

    Args:
        embedding_function: LangChain Embeddings instance
        vector_store_repo: Optional existing vector store repository
        search_type: Search strategy (currently only "similarity" supported)
        search_kwargs: Search configuration dict:
            - k: Number of results (default 5)
            - min_score: Minimum similarity score 0-1 (optional)
            - metadata_filters: Dict of metadata filters (optional)

    Returns:
        NBARetriever with hybrid scoring capabilities

    Example:
        >>> from langchain_google_genai import GoogleGenerativeAIEmbeddings
        >>> embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        >>> retriever = create_nba_retriever(
        ...     embedding_function=embeddings,
        ...     search_kwargs={"k": 5, "min_score": 0.5}
        ... )
        >>> docs = retriever.invoke("Why is LeBron great?")
    """
    if search_kwargs is None:
        search_kwargs = {"k": 5}

    # Create vector store wrapper
    vector_store = NBAVectorStore(
        embedding_function=embedding_function,
        vector_store_repo=vector_store_repo,
    )

    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

    logger.info(
        f"Created NBA retriever with {search_type} search (k={search_kwargs.get('k', 5)})"
    )

    return retriever
