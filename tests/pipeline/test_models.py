"""
FILE: test_pipeline_models.py
STATUS: Active
RESPONSIBILITY: Tests for pipeline stage Pydantic models validation
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import pickle

import pytest
from pydantic import ValidationError

from src.pipeline.models import (
    ChunkData,
    CleanedDocument,
    EmbedStageOutput,
    IndexStageOutput,
    LoadStageInput,
    LoadStageOutput,
    PipelineResult,
    QualityCheckResult,
    RawDocument,
)


class TestLoadStageInput:
    def test_valid_input(self):
        inp = LoadStageInput(input_dir="inputs")
        assert inp.input_dir == "inputs"
        assert inp.data_url is None

    def test_with_url(self):
        inp = LoadStageInput(input_dir="data", data_url="https://example.com/data.zip")
        assert inp.data_url == "https://example.com/data.zip"

    def test_empty_dir_raises(self):
        with pytest.raises(ValidationError):
            LoadStageInput(input_dir="")

    def test_path_traversal_raises(self):
        with pytest.raises(ValidationError, match="Path traversal"):
            LoadStageInput(input_dir="../etc/passwd")


class TestRawDocument:
    def test_valid_document(self):
        doc = RawDocument(page_content="Some content", metadata={"source": "test.txt"})
        assert doc.page_content == "Some content"

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError):
            RawDocument(page_content="")


class TestLoadStageOutput:
    def test_valid_output(self):
        out = LoadStageOutput(
            documents=[RawDocument(page_content="text")],
            document_count=1,
        )
        assert out.document_count == 1
        assert len(out.documents) == 1

    def test_with_errors(self):
        out = LoadStageOutput(
            documents=[],
            document_count=0,
            errors=["Download failed"],
        )
        assert len(out.errors) == 1


class TestCleanedDocument:
    def test_valid(self):
        doc = CleanedDocument(page_content="Clean text", char_count=10)
        assert doc.char_count == 10

    def test_zero_char_count_raises(self):
        with pytest.raises(ValidationError):
            CleanedDocument(page_content="a", char_count=0)


class TestChunkData:
    def test_valid_chunk(self):
        chunk = ChunkData(id="0_0", text="Chunk text", metadata={"source": "a.pdf"})
        assert chunk.id == "0_0"

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            ChunkData(id="0_0", text="")

    def test_empty_id_raises(self):
        with pytest.raises(ValidationError):
            ChunkData(id="", text="text")

    def test_chunk_with_data_type_metadata(self):
        """Test ChunkData with data_type metadata field."""
        chunk = ChunkData(
            id="0_0",
            text="LeBron James scored 30 points",
            metadata={
                "source": "player_stats.csv",
                "chunk_id_in_doc": 0,
                "data_type": "player_stats",
            },
        )
        assert chunk.metadata["data_type"] == "player_stats"
        assert chunk.metadata["source"] == "player_stats.csv"

    def test_chunk_metadata_accepts_any_type(self):
        """Test that metadata can contain various types including nested dicts."""
        chunk = ChunkData(
            id="0_0",
            text="Sample text",
            metadata={
                "source": "test.pdf",
                "chunk_id_in_doc": 0,
                "data_type": "player_stats",
                "nested": {"key": "value"},
                "number": 42,
                "float_val": 3.14,
            },
        )
        assert chunk.metadata["data_type"] == "player_stats"
        assert chunk.metadata["nested"]["key"] == "value"
        assert chunk.metadata["number"] == 42

    def test_chunk_with_data_type_serializes(self):
        """Test that ChunkData with data_type metadata can be pickled/unpickled."""
        chunk = ChunkData(
            id="0_0",
            text="LeBron James scored 30 points in Game 3",
            metadata={
                "source": "player_stats_2023.csv",
                "chunk_id_in_doc": 0,
                "total_chunks_in_doc": 5,
                "data_type": "player_stats",
            },
        )

        # Serialize as dict (matching VectorStoreRepository format)
        chunk_dict = {"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata}
        serialized = pickle.dumps(chunk_dict)

        # Deserialize
        deserialized_dict = pickle.loads(serialized)
        restored_chunk = ChunkData(**deserialized_dict)

        # Verify all fields preserved
        assert restored_chunk.id == chunk.id
        assert restored_chunk.text == chunk.text
        assert restored_chunk.metadata["data_type"] == "player_stats"
        assert restored_chunk.metadata["source"] == "player_stats_2023.csv"
        assert restored_chunk.metadata["chunk_id_in_doc"] == 0


class TestQualityCheckResult:
    def test_valid(self):
        result = QualityCheckResult(
            chunk_id="0_0",
            is_coherent=True,
            quality_score=0.95,
        )
        assert result.is_coherent is True

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            QualityCheckResult(chunk_id="0_0", is_coherent=True, quality_score=1.5)

    def test_with_issues(self):
        result = QualityCheckResult(
            chunk_id="0_0",
            is_coherent=False,
            quality_score=0.3,
            issues=["Truncated sentence", "Encoding artifact"],
        )
        assert len(result.issues) == 2


class TestEmbedStageOutput:
    def test_valid(self):
        out = EmbedStageOutput(embedding_count=100, embedding_dimension=1024)
        assert out.embedding_count == 100


class TestIndexStageOutput:
    def test_valid(self):
        out = IndexStageOutput(
            index_size=100,
            index_path="data/vector/faiss_index.idx",
            chunks_path="data/vector/document_chunks.pkl",
        )
        assert out.index_size == 100


class TestPipelineResult:
    def test_valid_result(self):
        result = PipelineResult(
            documents_loaded=10,
            documents_cleaned=9,
            chunks_created=50,
            embeddings_generated=50,
            index_size=50,
            processing_time_ms=1234.5,
        )
        assert result.documents_loaded == 10
        assert result.quality_checks_passed is None

    def test_with_quality_checks(self):
        result = PipelineResult(
            documents_loaded=10,
            documents_cleaned=9,
            chunks_created=50,
            embeddings_generated=50,
            index_size=50,
            quality_checks_passed=8,
            quality_checks_total=10,
            processing_time_ms=5000.0,
        )
        assert result.quality_checks_passed == 8

    def test_with_errors(self):
        result = PipelineResult(
            documents_loaded=0,
            documents_cleaned=0,
            chunks_created=0,
            embeddings_generated=0,
            index_size=0,
            processing_time_ms=100.0,
            errors=["No documents found"],
        )
        assert len(result.errors) == 1
