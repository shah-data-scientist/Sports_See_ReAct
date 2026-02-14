"""
FILE: document.py
STATUS: Active
RESPONSIBILITY: Pydantic models for documents and document chunks
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """Metadata for a document.

    Attributes:
        source: Source file path or identifier
        filename: Original filename
        category: Document category/folder
        page: Page number (for PDFs)
        sheet: Sheet name (for Excel)
    """

    source: str = Field(description="Source file path")
    filename: str = Field(description="Original filename")
    category: str = Field(default="root", description="Document category")
    page: int | None = Field(default=None, ge=1, description="Page number")
    sheet: str | None = Field(default=None, description="Excel sheet name")
    full_path: str | None = Field(default=None, description="Full file path")


class Document(BaseModel):
    """A parsed document with content and metadata.

    Attributes:
        page_content: Extracted text content
        metadata: Document metadata
    """

    page_content: str = Field(min_length=1, description="Document text content")
    metadata: DocumentMetadata = Field(description="Document metadata")

    @field_validator("page_content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Document content cannot be empty")
        return v


class DocumentChunk(BaseModel):
    """A chunk of a document with embedding information.

    Attributes:
        id: Unique chunk identifier
        text: Chunk text content
        metadata: Chunk metadata including position info
    """

    id: str = Field(description="Unique chunk identifier")
    text: str = Field(min_length=1, description="Chunk text content")
    metadata: dict[str, str | int | float] = Field(
        default_factory=dict,
        description="Chunk metadata",
    )

    @property
    def source(self) -> str:
        """Get source document identifier."""
        return self.metadata.get("source", "unknown")

    @property
    def chunk_index(self) -> int:
        """Get chunk index within document."""
        return int(self.metadata.get("chunk_id_in_doc", 0))


class IndexingRequest(BaseModel):
    """Request to index documents.

    Attributes:
        input_dir: Directory containing documents to index
        rebuild: Whether to rebuild index from scratch
        data_url: Optional URL to download documents from
    """

    input_dir: str = Field(
        default="inputs",
        description="Directory containing documents",
    )
    rebuild: bool = Field(
        default=False,
        description="Rebuild index from scratch",
    )
    data_url: str | None = Field(
        default=None,
        description="URL to download documents from (ZIP file)",
    )

    @field_validator("input_dir")
    @classmethod
    def validate_input_dir(cls, v: str) -> str:
        """Validate input directory path."""
        # Prevent path traversal
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        return v

    @field_validator("data_url")
    @classmethod
    def validate_data_url(cls, v: str | None) -> str | None:
        """Validate data URL if provided."""
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must use http:// or https://")
        return v


class IndexingResponse(BaseModel):
    """Response from indexing operation.

    Attributes:
        status: Operation status
        documents_processed: Number of documents processed
        chunks_created: Number of chunks created
        index_size: Total vectors in index
        processing_time_ms: Processing time in milliseconds
    """

    status: Literal["success", "partial", "failed"] = Field(
        description="Indexing status"
    )
    documents_processed: int = Field(ge=0, description="Documents processed")
    chunks_created: int = Field(ge=0, description="Chunks created")
    index_size: int = Field(ge=0, description="Total vectors in index")
    processing_time_ms: float = Field(ge=0, description="Processing time (ms)")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Operation timestamp (UTC)",
    )


class SupportedFileType(BaseModel):
    """Information about a supported file type.

    Attributes:
        extension: File extension
        mime_type: MIME type
        description: Human-readable description
        ocr_support: Whether OCR is available
    """

    extension: str = Field(description="File extension (e.g., '.pdf')")
    mime_type: str = Field(description="MIME type")
    description: str = Field(description="Human-readable description")
    ocr_support: bool = Field(default=False, description="OCR availability")


# Supported file types
SUPPORTED_FILE_TYPES: list[SupportedFileType] = [
    SupportedFileType(
        extension=".pdf",
        mime_type="application/pdf",
        description="PDF Document",
        ocr_support=True,
    ),
    SupportedFileType(
        extension=".docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        description="Word Document",
        ocr_support=False,
    ),
    SupportedFileType(
        extension=".txt",
        mime_type="text/plain",
        description="Plain Text",
        ocr_support=False,
    ),
    SupportedFileType(
        extension=".csv",
        mime_type="text/csv",
        description="CSV File",
        ocr_support=False,
    ),
    SupportedFileType(
        extension=".xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        description="Excel Spreadsheet",
        ocr_support=False,
    ),
    SupportedFileType(
        extension=".xls",
        mime_type="application/vnd.ms-excel",
        description="Excel Spreadsheet (Legacy)",
        ocr_support=False,
    ),
]
