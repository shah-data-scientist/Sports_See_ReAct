"""
FILE: test_document.py
STATUS: Active
RESPONSIBILITY: Unit tests for document models (Document, DocumentChunk, IndexingRequest, etc.)
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.models.document import (
    Document,
    DocumentChunk,
    DocumentMetadata,
    IndexingRequest,
    IndexingResponse,
    SupportedFileType,
    SUPPORTED_FILE_TYPES,
)


class TestDocumentMetadata:
    def test_basic_metadata(self):
        meta = DocumentMetadata(source="test.pdf", filename="test.pdf")
        assert meta.source == "test.pdf"
        assert meta.category == "root"
        assert meta.page is None
        assert meta.sheet is None

    def test_metadata_with_optional_fields(self):
        meta = DocumentMetadata(
            source="data.xlsx",
            filename="data.xlsx",
            category="stats",
            page=3,
            sheet="Sheet1",
            full_path="/data/data.xlsx",
        )
        assert meta.page == 3
        assert meta.sheet == "Sheet1"
        assert meta.full_path == "/data/data.xlsx"


class TestDocument:
    def test_valid_document(self):
        meta = DocumentMetadata(source="test.pdf", filename="test.pdf")
        doc = Document(page_content="This is test content.", metadata=meta)
        assert doc.page_content == "This is test content."

    def test_content_stripped(self):
        meta = DocumentMetadata(source="test.pdf", filename="test.pdf")
        doc = Document(page_content="  hello world  ", metadata=meta)
        assert doc.page_content == "hello world"

    def test_empty_content_raises(self):
        meta = DocumentMetadata(source="test.pdf", filename="test.pdf")
        with pytest.raises(Exception):
            Document(page_content="   ", metadata=meta)


class TestDocumentChunk:
    def test_basic_chunk(self):
        chunk = DocumentChunk(id="chunk_1", text="Some text here")
        assert chunk.id == "chunk_1"
        assert chunk.text == "Some text here"

    def test_source_property_default(self):
        chunk = DocumentChunk(id="c1", text="text")
        assert chunk.source == "unknown"

    def test_source_property_from_metadata(self):
        chunk = DocumentChunk(id="c1", text="text", metadata={"source": "file.pdf"})
        assert chunk.source == "file.pdf"

    def test_chunk_index_property(self):
        chunk = DocumentChunk(id="c1", text="text", metadata={"chunk_id_in_doc": 5})
        assert chunk.chunk_index == 5

    def test_chunk_index_default(self):
        chunk = DocumentChunk(id="c1", text="text")
        assert chunk.chunk_index == 0


class TestIndexingRequest:
    def test_default_values(self):
        req = IndexingRequest()
        assert req.input_dir == "inputs"
        assert req.rebuild is False
        assert req.data_url is None

    def test_path_traversal_blocked(self):
        with pytest.raises(Exception):
            IndexingRequest(input_dir="../../../etc")

    def test_invalid_url_rejected(self):
        with pytest.raises(Exception):
            IndexingRequest(data_url="ftp://example.com/data.zip")

    def test_valid_url_accepted(self):
        req = IndexingRequest(data_url="https://example.com/data.zip")
        assert req.data_url == "https://example.com/data.zip"


class TestIndexingResponse:
    def test_success_response(self):
        resp = IndexingResponse(
            status="success",
            documents_processed=10,
            chunks_created=50,
            index_size=50,
            processing_time_ms=1234.5,
        )
        assert resp.status == "success"
        assert resp.documents_processed == 10
        assert resp.errors == []


class TestSupportedFileTypes:
    def test_supported_file_types_count(self):
        assert len(SUPPORTED_FILE_TYPES) == 6

    def test_pdf_has_ocr_support(self):
        pdf = next(f for f in SUPPORTED_FILE_TYPES if f.extension == ".pdf")
        assert pdf.ocr_support is True

    def test_txt_no_ocr_support(self):
        txt = next(f for f in SUPPORTED_FILE_TYPES if f.extension == ".txt")
        assert txt.ocr_support is False
