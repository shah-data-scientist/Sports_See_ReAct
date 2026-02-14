"""
FILE: embedding.py
STATUS: Active
RESPONSIBILITY: Mistral AI embedding service for vector generation
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import logging
from collections.abc import Sequence

import numpy as np
from mistralai import Mistral
from mistralai.models import SDKError

from src.core.config import settings
from src.core.exceptions import EmbeddingError
from src.core.observability import logfire

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings via Mistral API.

    Handles batching, error recovery, and provides a clean interface
    for embedding generation.

    Attributes:
        model: Embedding model name
        batch_size: Batch size for API calls
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        batch_size: int | None = None,
    ):
        """Initialize embedding service.

        Args:
            api_key: Mistral API key (default from settings)
            model: Embedding model name (default from settings)
            batch_size: Batch size for API calls (default from settings)
        """
        self._api_key = api_key or settings.mistral_api_key
        self._model = model or settings.embedding_model
        self._batch_size = batch_size or settings.embedding_batch_size
        self._client: Mistral | None = None

    @property
    def client(self) -> Mistral:
        """Get or create Mistral client (lazy initialization)."""
        if self._client is None:
            self._client = Mistral(api_key=self._api_key)
        return self._client

    @property
    def model(self) -> str:
        """Get embedding model name."""
        return self._model

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array

        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = self.embed_batch([text])
        return embeddings[0]

    @logfire.instrument("EmbeddingService.embed_batch")
    def embed_batch(self, texts: Sequence[str]) -> np.ndarray:
        """Generate embeddings for multiple texts.

        Handles batching automatically based on batch_size setting.

        Args:
            texts: Sequence of texts to embed

        Returns:
            Embeddings array (n_texts x embedding_dim)

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            raise EmbeddingError("No texts provided for embedding")

        texts_list = list(texts)
        all_embeddings: list[list[float]] = []

        total_batches = (len(texts_list) + self._batch_size - 1) // self._batch_size
        logger.info(
            "Generating embeddings for %d texts in %d batches",
            len(texts_list),
            total_batches,
        )

        for i in range(0, len(texts_list), self._batch_size):
            batch = texts_list[i : i + self._batch_size]
            batch_num = (i // self._batch_size) + 1

            try:
                logger.debug(
                    "Processing batch %d/%d (%d texts)",
                    batch_num,
                    total_batches,
                    len(batch),
                )

                response = self.client.embeddings.create(
                    model=self._model,
                    inputs=batch,
                )

                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

            except SDKError as e:
                logger.error(
                    "Mistral API error in batch %d: %s",
                    batch_num,
                    e,
                )
                raise EmbeddingError(
                    f"Embedding API error: {e}",
                    details={"batch": batch_num},
                ) from e

            except Exception as e:
                logger.error("Unexpected error in batch %d: %s", batch_num, e)
                raise EmbeddingError(
                    f"Embedding failed: {e}",
                    details={"batch": batch_num},
                ) from e

        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        logger.info(
            "Generated embeddings with shape %s",
            embeddings_array.shape,
        )

        return embeddings_array

    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a search query.

        This is an alias for embed_single, provided for semantic clarity.

        Args:
            query: Search query text

        Returns:
            Query embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        return self.embed_single(query)
