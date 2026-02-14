"""
FILE: test_embedding.py
STATUS: Active
RESPONSIBILITY: Unit tests for EmbeddingService - Mistral embedding generation
LAST MAJOR UPDATE: 2026-02-08
MAINTAINER: Shahu
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from mistralai.models import SDKError

from src.core.exceptions import EmbeddingError
from src.services.embedding import EmbeddingService


class TestEmbeddingServiceInit:
    """Test EmbeddingService initialization."""

    @patch("src.services.embedding.settings")
    def test_init_default_params(self, mock_settings):
        """Test initialization with default parameters."""
        mock_settings.mistral_api_key = "test_key"
        mock_settings.embedding_model = "mistral-embed"
        mock_settings.embedding_batch_size = 32

        service = EmbeddingService()

        assert service._api_key == "test_key"
        assert service._model == "mistral-embed"
        assert service._batch_size == 32
        assert service._client is None  # Lazy initialization

    def test_init_custom_api_key(self):
        """Test initialization with custom API key."""
        service = EmbeddingService(api_key="custom_key_123")

        assert service._api_key == "custom_key_123"

    def test_init_custom_model(self):
        """Test initialization with custom model."""
        service = EmbeddingService(model="custom-embed-model")

        assert service._model == "custom-embed-model"

    def test_init_custom_batch_size(self):
        """Test initialization with custom batch size."""
        service = EmbeddingService(batch_size=64)

        assert service._batch_size == 64

    def test_init_all_custom_params(self):
        """Test initialization with all custom parameters."""
        service = EmbeddingService(
            api_key="key123",
            model="test-model",
            batch_size=128,
        )

        assert service._api_key == "key123"
        assert service._model == "test-model"
        assert service._batch_size == 128


class TestClientProperty:
    """Test lazy client initialization."""

    @patch("src.services.embedding.Mistral")
    def test_client_lazy_initialization(self, mock_mistral_class):
        """Test client is initialized on first access."""
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        service = EmbeddingService(api_key="test_key")

        # Client should be None initially
        assert service._client is None

        # Access client property
        client = service.client

        # Client should be initialized
        assert client is mock_client
        mock_mistral_class.assert_called_once_with(api_key="test_key")

    @patch("src.services.embedding.Mistral")
    def test_client_cached_after_first_access(self, mock_mistral_class):
        """Test client is cached and not recreated on subsequent access."""
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        service = EmbeddingService(api_key="test_key")

        # Access client multiple times
        client1 = service.client
        client2 = service.client
        client3 = service.client

        # Should only create client once
        mock_mistral_class.assert_called_once()

        # All references should be the same
        assert client1 is client2
        assert client2 is client3


class TestModelProperty:
    """Test model property."""

    def test_model_property_returns_model_name(self):
        """Test model property returns the configured model name."""
        service = EmbeddingService(model="test-embed-v1")

        assert service.model == "test-embed-v1"


class TestEmbedSingle:
    """Test single text embedding."""

    @patch("src.services.embedding.Mistral")
    def test_embed_single_success(self, mock_mistral_class):
        """Test successful single text embedding."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_data = Mock()
        mock_data.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_response = Mock()
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test_key")

        # Test
        result = service.embed_single("Test text")

        # Verify
        assert isinstance(result, np.ndarray)
        assert result.shape == (5,)
        assert np.allclose(result, [0.1, 0.2, 0.3, 0.4, 0.5])

        # Verify API call
        mock_client.embeddings.create.assert_called_once_with(
            model=service._model,
            inputs=["Test text"],
        )


class TestEmbedBatch:
    """Test batch embedding."""

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_single_batch(self, mock_mistral_class):
        """Test batch embedding with texts fitting in single batch."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_data1 = Mock()
        mock_data1.embedding = [0.1, 0.2, 0.3]
        mock_data2 = Mock()
        mock_data2.embedding = [0.4, 0.5, 0.6]
        mock_response = Mock()
        mock_response.data = [mock_data1, mock_data2]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test_key", batch_size=32)

        # Test with 2 texts (< batch_size)
        texts = ["Text 1", "Text 2"]
        result = service.embed_batch(texts)

        # Verify
        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 3)
        assert np.allclose(result[0], [0.1, 0.2, 0.3])
        assert np.allclose(result[1], [0.4, 0.5, 0.6])

        # Verify single API call
        mock_client.embeddings.create.assert_called_once()

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_multiple_batches(self, mock_mistral_class):
        """Test batch embedding with texts spanning multiple batches."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        # First batch response (3 texts)
        mock_response1 = Mock()
        mock_response1.data = [
            Mock(embedding=[0.1, 0.2]),
            Mock(embedding=[0.3, 0.4]),
            Mock(embedding=[0.5, 0.6]),
        ]

        # Second batch response (2 texts)
        mock_response2 = Mock()
        mock_response2.data = [
            Mock(embedding=[0.7, 0.8]),
            Mock(embedding=[0.9, 1.0]),
        ]

        mock_client.embeddings.create.side_effect = [mock_response1, mock_response2]

        service = EmbeddingService(api_key="test_key", batch_size=3)

        # Test with 5 texts (requires 2 batches: 3 + 2)
        texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
        result = service.embed_batch(texts)

        # Verify
        assert isinstance(result, np.ndarray)
        assert result.shape == (5, 2)
        assert np.allclose(result[0], [0.1, 0.2])
        assert np.allclose(result[4], [0.9, 1.0])

        # Verify two API calls
        assert mock_client.embeddings.create.call_count == 2

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_exact_batch_size(self, mock_mistral_class):
        """Test batch embedding with texts exactly matching batch size."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1]),
            Mock(embedding=[0.2]),
            Mock(embedding=[0.3]),
        ]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test_key", batch_size=3)

        # Test with exactly 3 texts
        texts = ["Text 1", "Text 2", "Text 3"]
        result = service.embed_batch(texts)

        # Verify
        assert result.shape == (3, 1)
        assert mock_client.embeddings.create.call_count == 1

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_empty_texts_raises_error(self, mock_mistral_class):
        """Test batch embedding raises error for empty texts list."""
        mock_mistral_class.return_value = MagicMock()

        service = EmbeddingService(api_key="test_key")

        with pytest.raises(EmbeddingError, match="No texts provided"):
            service.embed_batch([])

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_sdk_error(self, mock_mistral_class):
        """Test batch embedding handles SDKError."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        # Create proper httpx.Response mock
        mock_raw_response = Mock()
        mock_raw_response.status_code = 429
        mock_raw_response.text = "Rate limit exceeded"
        mock_raw_response.headers = {"content-type": "application/json"}

        mock_client.embeddings.create.side_effect = SDKError(
            "API rate limit exceeded",
            raw_response=mock_raw_response
        )

        service = EmbeddingService(api_key="test_key")

        # Test
        with pytest.raises(EmbeddingError, match="Embedding API error"):
            service.embed_batch(["Test text"])

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_generic_error(self, mock_mistral_class):
        """Test batch embedding handles generic exceptions."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_client.embeddings.create.side_effect = ValueError("Invalid input")

        service = EmbeddingService(api_key="test_key")

        # Test
        with pytest.raises(EmbeddingError, match="Embedding failed"):
            service.embed_batch(["Test text"])

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_error_in_second_batch(self, mock_mistral_class):
        """Test batch embedding handles error in second batch."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        # First batch succeeds
        mock_response1 = Mock()
        mock_response1.data = [Mock(embedding=[0.1, 0.2])]

        # Second batch fails
        mock_raw_response = Mock()
        mock_raw_response.status_code = 500
        mock_raw_response.text = "Internal server error"
        mock_raw_response.headers = {"content-type": "application/json"}

        mock_client.embeddings.create.side_effect = [
            mock_response1,
            SDKError("Network error", raw_response=mock_raw_response),
        ]

        service = EmbeddingService(api_key="test_key", batch_size=1)

        # Test with 2 texts (2 batches)
        with pytest.raises(EmbeddingError, match="Embedding API error"):
            service.embed_batch(["Text 1", "Text 2"])

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_returns_float32_array(self, mock_mistral_class):
        """Test batch embedding returns numpy array with float32 dtype."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_data = Mock()
        mock_data.embedding = [0.1, 0.2, 0.3]
        mock_response = Mock()
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test_key")

        # Test
        result = service.embed_batch(["Test text"])

        # Verify dtype
        assert result.dtype == np.float32

    @patch("src.services.embedding.Mistral")
    def test_embed_batch_with_large_batch(self, mock_mistral_class):
        """Test batch embedding with many texts."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        # Mock responses for 4 batches (10 texts, batch_size=3 → 4 batches)
        def create_response(start_idx, count):
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[float(start_idx + i)]) for i in range(count)
            ]
            return mock_response

        mock_client.embeddings.create.side_effect = [
            create_response(0, 3),  # Batch 1: 3 texts
            create_response(3, 3),  # Batch 2: 3 texts
            create_response(6, 3),  # Batch 3: 3 texts
            create_response(9, 1),  # Batch 4: 1 text
        ]

        service = EmbeddingService(api_key="test_key", batch_size=3)

        # Test with 10 texts
        texts = [f"Text {i}" for i in range(10)]
        result = service.embed_batch(texts)

        # Verify
        assert result.shape == (10, 1)
        assert mock_client.embeddings.create.call_count == 4


class TestEmbedQuery:
    """Test query embedding (alias for embed_single)."""

    @patch("src.services.embedding.Mistral")
    def test_embed_query_calls_embed_single(self, mock_mistral_class):
        """Test embed_query is an alias for embed_single."""
        # Setup mock
        mock_client = MagicMock()
        mock_mistral_class.return_value = mock_client

        mock_data = Mock()
        mock_data.embedding = [0.1, 0.2, 0.3]
        mock_response = Mock()
        mock_response.data = [mock_data]
        mock_client.embeddings.create.return_value = mock_response

        service = EmbeddingService(api_key="test_key")

        # Test
        result = service.embed_query("Search query")

        # Verify
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)
        assert np.allclose(result, [0.1, 0.2, 0.3])

        # Verify API call with query text
        mock_client.embeddings.create.assert_called_once_with(
            model=service._model,
            inputs=["Search query"],
        )
