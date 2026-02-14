"""
FILE: test_data_loader.py
STATUS: Active
RESPONSIBILITY: Tests for document loading and parsing utilities
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import tempfile
from pathlib import Path

import pytest


def test_data_loader_imports():
    """Test that data_loader module can be imported."""
    from src.utils import data_loader

    assert data_loader is not None


def test_extract_text_from_txt():
    """Test text extraction from TXT files."""
    from src.utils.data_loader import extract_text_from_txt

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Test content")
        temp_path = f.name

    try:
        text = extract_text_from_txt(temp_path)
        assert text == "Test content"
    finally:
        Path(temp_path).unlink()


def test_extract_text_from_txt_nonexistent():
    """Test text extraction from non-existent file."""
    from src.utils.data_loader import extract_text_from_txt

    result = extract_text_from_txt("/nonexistent/file.txt")
    assert result is None


def test_load_and_parse_files_empty_dir():
    """Test loading files from empty directory."""
    from src.utils.data_loader import load_and_parse_files

    with tempfile.TemporaryDirectory() as temp_dir:
        documents = load_and_parse_files(temp_dir)
        assert isinstance(documents, list)
        assert len(documents) == 0


def test_load_and_parse_files_with_txt():
    """Test loading files from directory with TXT file."""
    from src.utils.data_loader import load_and_parse_files

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test TXT file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("NBA statistics content")

        documents = load_and_parse_files(temp_dir)
        assert isinstance(documents, list)
        assert len(documents) == 1
        assert "NBA statistics content" in documents[0]["page_content"]
        assert "metadata" in documents[0]
        assert "source" in documents[0]["metadata"]
