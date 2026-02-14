"""
FILE: test_data_pipeline.py
STATUS: Active
RESPONSIBILITY: Tests for data preparation pipeline logic with mocked services (includes integration tests)
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.pipeline.data_pipeline import DataPipeline
from src.pipeline.models import (
    ChunkData,
    CleanedDocument,
    LoadStageInput,
    QualityCheckResult,
    RawDocument,
)


@pytest.fixture
def mock_embedding_service():
    service = MagicMock()
    service.embed_batch.return_value = np.random.rand(5, 64).astype(np.float32)
    return service


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.index_size = 5
    store.build_index.return_value = None
    store.save.return_value = None
    return store


@pytest.fixture
def pipeline(mock_embedding_service, mock_vector_store):
    return DataPipeline(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        enable_quality_check=False,
    )


class TestDataPipelineLoad:
    def test_load_from_directory(self, pipeline):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("NBA statistics content for testing purposes.")

            result = pipeline.load(LoadStageInput(input_dir=temp_dir))

            assert result.document_count >= 1
            assert len(result.documents) >= 1
            assert result.documents[0].page_content

    def test_load_empty_directory(self, pipeline):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.load(LoadStageInput(input_dir=temp_dir))
            assert result.document_count == 0


class TestDataPipelineClean:
    def test_clean_removes_short_docs(self, pipeline):
        docs = [
            RawDocument(page_content="Short"),
            RawDocument(page_content="This is a longer document with enough content."),
        ]
        result = pipeline.clean(docs)
        assert result.removed_count == 1
        assert len(result.documents) == 1

    def test_clean_strips_whitespace(self, pipeline):
        docs = [RawDocument(page_content="  Padded content with spaces  ")]
        result = pipeline.clean(docs)
        assert result.documents[0].page_content == "Padded content with spaces"

    def test_clean_all_valid(self, pipeline):
        docs = [
            RawDocument(page_content="First valid document content."),
            RawDocument(page_content="Second valid document content."),
        ]
        result = pipeline.clean(docs)
        assert result.removed_count == 0
        assert len(result.documents) == 2
        assert result.total_chars > 0


class TestDataPipelineChunk:
    def test_chunk_splits_text(self, pipeline):
        docs = [
            CleanedDocument(
                page_content="A " * 1000,
                char_count=2000,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunk_count > 1
        assert all(isinstance(c, ChunkData) for c in result.chunks)

    def test_chunk_preserves_metadata(self, pipeline):
        docs = [
            CleanedDocument(
                page_content="Content " * 200,
                metadata={"source": "test.pdf"},
                char_count=1600,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunks[0].metadata.get("source") == "test.pdf"
        assert "chunk_id_in_doc" in result.chunks[0].metadata

    def test_chunk_tags_data_type_player_stats(self, pipeline):
        """Test that chunks from player stats files are tagged with data_type='player_stats'."""
        docs = [
            CleanedDocument(
                page_content="LeBron James 28.5 PTS 7.3 REB 8.1 AST 50.2 FG%. " * 50,
                metadata={"source": "player_stats_2023.csv"},
                char_count=2050,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunk_count > 0
        assert result.chunks[0].metadata.get("data_type") == "player_stats"

    def test_chunk_tags_data_type_team_stats(self, pipeline):
        """Test that chunks from team stats files are tagged with data_type='team_stats'."""
        docs = [
            CleanedDocument(
                page_content="Lakers won 112-108 against the Celtics. " * 50,
                metadata={"source": "team_performance.xlsx"},
                char_count=2000,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunk_count > 0
        assert result.chunks[0].metadata.get("data_type") == "team_stats"

    def test_chunk_tags_data_type_game_data(self, pipeline):
        """Test that chunks from schedule/game files are tagged with data_type='game_data'."""
        docs = [
            CleanedDocument(
                page_content="Game scheduled for 7:30 PM at Staples Center. " * 50,
                metadata={"source": "schedule_2023.pdf"},
                char_count=2350,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunk_count > 0
        assert result.chunks[0].metadata.get("data_type") == "game_data"

    def test_chunk_tags_data_type_unknown(self, pipeline):
        """Test that chunks from unrecognized files are tagged with data_type='discussion'."""
        docs = [
            CleanedDocument(
                page_content="Some random content that doesn't match any pattern. " * 50,
                metadata={"source": "random_document.txt"},
                char_count=2650,
            ),
        ]
        result = pipeline.chunk(docs, chunk_size=500, chunk_overlap=50)
        assert result.chunk_count > 0
        assert result.chunks[0].metadata.get("data_type") == "discussion"

    def test_chunk_empty_input(self, pipeline):
        result = pipeline.chunk([])
        assert result.chunk_count == 0


class TestDataPipelineQualityCheck:
    @patch("src.pipeline.quality_agent.check_chunk_quality")
    def test_quality_check_samples_chunks(
        self, mock_check, mock_embedding_service, mock_vector_store
    ):
        pipeline = DataPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            enable_quality_check=True,
            quality_sample_size=2,
        )

        mock_check.return_value = QualityCheckResult(
            chunk_id="0_0",
            is_coherent=True,
            quality_score=0.9,
        )

        chunks = [ChunkData(id=f"0_{i}", text=f"Chunk text {i}") for i in range(5)]
        results = pipeline.quality_check(chunks)

        assert len(results) == 2
        assert mock_check.call_count == 2


class TestDataPipelineEmbed:
    def test_embed_returns_metadata(self, pipeline, mock_embedding_service):
        mock_embedding_service.embed_batch.return_value = np.random.rand(3, 64).astype(np.float32)
        output, embeddings = pipeline.embed(["text1", "text2", "text3"])

        assert output.embedding_count == 3
        assert output.embedding_dimension == 64
        assert embeddings.shape == (3, 64)


class TestDataPipelineIndex:
    def test_index_builds_and_saves(self, pipeline, mock_vector_store):
        mock_vector_store.index_size = 3

        chunks = [ChunkData(id=f"0_{i}", text=f"Chunk {i}") for i in range(3)]
        embeddings = np.random.rand(3, 64).astype(np.float32)

        result = pipeline.index(chunks, embeddings)

        assert result.index_size == 3
        mock_vector_store.build_index.assert_called_once()
        mock_vector_store.save.assert_called_once()


class TestDataPipelineRun:
    def test_run_end_to_end(self, mock_embedding_service, mock_vector_store):
        mock_embedding_service.embed_batch.return_value = np.random.rand(5, 64).astype(np.float32)
        mock_vector_store.index_size = 5

        pipeline = DataPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("NBA content " * 200)

            result = pipeline.run(input_dir=temp_dir)

            assert result.documents_loaded >= 1
            assert result.chunks_created >= 1
            assert result.embeddings_generated >= 1
            assert result.processing_time_ms > 0

    def test_run_empty_directory(self, mock_embedding_service, mock_vector_store):
        pipeline = DataPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = pipeline.run(input_dir=temp_dir)

            assert result.documents_loaded == 0
            assert "No documents found" in result.errors


# Integration Tests (formerly test_data_pipeline_integration.py)


class TestDataPipelineLoad:
    """Integration tests for DataPipeline load stage."""

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    @patch("src.pipeline.data_pipeline.load_and_parse_files")
    def test_load_stage_returns_documents(self, mock_load, mock_embed, mock_vs):
        """Test load stage returns parsed documents."""
        mock_load.return_value = [
            {"page_content": "Some NBA content here", "metadata": {"source": "test.pdf"}},
        ]

        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        input_data = LoadStageInput(input_dir="test_inputs")
        result = pipeline.load(input_data)

        assert result.document_count == 1
        assert len(result.documents) == 1
        assert result.documents[0].page_content == "Some NBA content here"

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    @patch("src.pipeline.data_pipeline.load_and_parse_files")
    def test_load_stage_skips_empty_docs(self, mock_load, mock_embed, mock_vs):
        """Test load stage skips empty documents."""
        mock_load.return_value = [
            {"page_content": "", "metadata": {}},
            {"page_content": "   ", "metadata": {}},
            {"page_content": "Valid content here", "metadata": {}},
        ]

        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        input_data = LoadStageInput(input_dir="test_inputs")
        result = pipeline.load(input_data)

        assert result.document_count == 1


class TestDataPipelineClean:
    """Integration tests for DataPipeline clean stage."""

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    def test_clean_removes_short_documents(self, mock_embed, mock_vs):
        """Test clean stage removes short documents."""
        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        docs = [
            RawDocument(page_content="short", metadata={}),
            RawDocument(page_content="This is a long enough document to pass filtering.", metadata={}),
        ]
        result = pipeline.clean(docs)

        assert len(result.documents) == 1
        assert result.removed_count == 1

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    def test_clean_computes_total_chars(self, mock_embed, mock_vs):
        """Test clean stage computes total character count."""
        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        docs = [
            RawDocument(page_content="A" * 100, metadata={}),
            RawDocument(page_content="B" * 200, metadata={}),
        ]
        result = pipeline.clean(docs)

        assert result.total_chars == 300


class TestDataPipelineAnalyzeContent:
    """Integration tests for content analysis."""

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    def test_player_stats_detection(self, mock_embed, mock_vs):
        """Test detection of player stats content."""
        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        text = "LeBron James scored 25 PTS with 10 AST and 8 REB in the game."
        result = pipeline._analyze_chunk_content(text)
        assert result == "player_stats"

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    def test_discussion_detection(self, mock_embed, mock_vs):
        """Test detection of discussion content."""
        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        text = "The evolution of modern basketball has been truly remarkable in many ways."
        result = pipeline._analyze_chunk_content(text)
        assert result == "discussion"


class TestDataPipelineFilterLowQuality:
    """Integration tests for quality filtering."""

    @patch("src.pipeline.data_pipeline.VectorStoreRepository")
    @patch("src.pipeline.data_pipeline.EmbeddingService")
    def test_filters_high_nan_chunks(self, mock_embed, mock_vs):
        """Test filtering of chunks with high NaN density."""
        pipeline = DataPipeline(
            embedding_service=mock_embed.return_value,
            vector_store=mock_vs.return_value,
        )
        chunks = [
            ChunkData(id="good", text="A" * 200, metadata={}),
            ChunkData(id="bad", text="NaN " * 100, metadata={}),
        ]
        filtered = pipeline._filter_low_quality_chunks(chunks)
        assert len(filtered) == 1
        assert filtered[0].id == "good"


class TestQualityThresholdFiltering:
    """Tests for quality score enrichment and threshold filtering."""

    def test_filter_removes_low_quality_chunks(self):
        """Chunks below threshold are removed."""
        pipeline = DataPipeline(
            embedding_service=MagicMock(),
            vector_store=MagicMock(),
            quality_threshold=0.5,
        )
        chunks = [
            ChunkData(id="high", text="Good text", metadata={"quality_score": 0.90}),
            ChunkData(id="mid", text="OK text", metadata={"quality_score": 0.50}),
            ChunkData(id="low", text="Bad text", metadata={"quality_score": 0.40}),
        ]
        filtered = pipeline._filter_by_quality_threshold(chunks)
        assert len(filtered) == 2
        assert [c.id for c in filtered] == ["high", "mid"]

    def test_filter_removes_unscored_chunks(self):
        """Chunks without quality_score are removed."""
        pipeline = DataPipeline(
            embedding_service=MagicMock(),
            vector_store=MagicMock(),
            quality_threshold=0.5,
        )
        chunks = [
            ChunkData(id="scored", text="Good text", metadata={"quality_score": 0.75}),
            ChunkData(id="unscored", text="No score", metadata={"source": "test.pdf"}),
        ]
        filtered = pipeline._filter_by_quality_threshold(chunks)
        assert len(filtered) == 1
        assert filtered[0].id == "scored"

    def test_filter_keeps_exact_threshold(self):
        """Chunks at exactly the threshold are kept."""
        pipeline = DataPipeline(
            embedding_service=MagicMock(),
            vector_store=MagicMock(),
            quality_threshold=0.5,
        )
        chunks = [
            ChunkData(id="exact", text="Borderline", metadata={"quality_score": 0.5}),
        ]
        filtered = pipeline._filter_by_quality_threshold(chunks)
        assert len(filtered) == 1

    def test_enrichment_loads_scores(self, tmp_path):
        """Quality enrichment adds scores to chunk metadata."""
        import json

        # Create mock scores file
        scores_file = tmp_path / "chunk_quality_scores.json"
        scores_file.write_text(json.dumps({
            "summary": {},
            "chunks": [
                {"chunk_id": 0, "quality_score": 0.90},
                {"chunk_id": 1, "quality_score": 0.75},
            ],
        }), encoding="utf-8")

        pipeline = DataPipeline(
            embedding_service=MagicMock(),
            vector_store=MagicMock(),
        )
        chunks = [
            ChunkData(id="c0", text="Text A", metadata={}),
            ChunkData(id="c1", text="Text B", metadata={}),
        ]

        # Patch pathlib.Path inside the method's local import
        from unittest.mock import MagicMock as MM
        original_path = Path

        class FakePath(type(Path())):
            def __new__(cls, *args, **kwargs):
                if args and "chunk_quality_scores" in str(args[0]):
                    return original_path.__new__(cls, str(scores_file))
                return original_path.__new__(cls, *args, **kwargs)

        with patch("pathlib.Path", FakePath):
            enriched = pipeline._enrich_quality_scores(chunks)

        assert enriched[0].metadata["quality_score"] == 0.90
        assert enriched[1].metadata["quality_score"] == 0.75
