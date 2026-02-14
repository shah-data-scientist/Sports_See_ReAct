"""
FILE: test_reddit_chunker.py
STATUS: Active
RESPONSIBILITY: Tests for Reddit 1-comment-per-chunk with metadata and ad filtering
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import pytest

from src.pipeline.reddit_chunker import RedditThreadChunker


# ---------------------------------------------------------------------------
# Fixtures: realistic Reddit thread OCR text
# ---------------------------------------------------------------------------

def _build_reddit_text(
    title: str = "Who is the best center in the NBA right now?",
    author: str = "BasketballFan99",
    post_body: str = "I think it's between Jokic and Embiid but curious what everyone thinks.",
    upvotes: int = 350,
    num_comments: int = 45,
    comments: list[dict] | None = None,
) -> str:
    """Build realistic Reddit thread OCR text for testing.

    Args:
        title: Post title
        author: Post author username
        post_body: Post body text (between author and stats)
        upvotes: Post upvotes
        num_comments: Comment count shown in stats
        comments: List of dicts with author, text, upvotes keys

    Returns:
        Simulated OCR text matching Reddit PDF patterns
    """
    if comments is None:
        comments = [
            {"author": "HoopHead42", "text": "Jokic is the clear number one, his passing is unmatched for a big man", "upvotes": 120},
            {"author": "EmbiidFan", "text": "Embiid when healthy is the most dominant center we have seen in years", "upvotes": 95},
            {"author": "NuggetsFan", "text": "Jokic literally won back to back MVPs, this should not be a debate anymore", "upvotes": 80},
            {"author": "Lakers", "text": "AD is underrated in this conversation, he anchors our defense", "upvotes": 60},
            {"author": "AnalystPro", "text": "If we go by advanced stats Jokic has the best PER and BPM of any center", "upvotes": 45},
            {"author": "CelticsFan", "text": "Horford may not be the best but he still contributes at a high level", "upvotes": 30},
            {"author": "RookieWatcher", "text": "Wembanyama is going to be in this conversation very soon", "upvotes": 25},
        ]

    text = f"r/nba\n{title}\nil y a 2 heures\n"
    text += f"{author}\n{title}\n"
    text += f"{post_body}\n"
    text += f"{upvotes}\n{num_comments}\nPartager\n\n"

    for c in comments:
        text += f"{c['author']}\n{c['text']}\n{c['upvotes']}\nRépondre\n\n"

    return text


@pytest.fixture
def chunker():
    """Default Reddit thread chunker (1-comment-per-chunk)."""
    return RedditThreadChunker()


@pytest.fixture
def sample_text():
    """Standard 7-comment Reddit thread text."""
    return _build_reddit_text()


# ---------------------------------------------------------------------------
# Tests: 1-comment-per-chunk
# ---------------------------------------------------------------------------

class TestOneCommentPerChunk:
    """Test 1-comment-per-chunk implementation."""

    def test_one_chunk_per_comment(self, chunker, sample_text):
        """7 comments → 7 chunks (1-to-1 mapping)."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        assert len(chunks) == 7

    def test_all_comments_preserved(self, chunker, sample_text):
        """All 7 comments appear (1 per chunk)."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        # Each chunk has exactly 1 comment
        assert len(chunks) == 7
        # Check unique comment authors
        authors = {c.metadata["comment_author"] for c in chunks}
        assert len(authors) == 7

    def test_first_chunk_has_highest_upvotes(self, chunker, sample_text):
        """First chunk has highest upvoted comment (sorted descending)."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        first_upvotes = chunks[0].metadata["comment_upvotes"]
        last_upvotes = chunks[-1].metadata["comment_upvotes"]
        assert first_upvotes >= last_upvotes

    def test_post_context_in_every_chunk(self, chunker, sample_text):
        """Every chunk contains post context (title, author, body)."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            assert "=== REDDIT POST ===" in chunk.text
            assert "Who is the best center" in chunk.text
            assert "u/" in chunk.text

    def test_comment_labels_sequential(self, chunker, sample_text):
        """Each chunk has correct comment label (COMMENT 1/7, COMMENT 2/7, etc.)."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for i, chunk in enumerate(chunks):
            assert f"COMMENT ({i + 1}/{len(chunks)})" in chunk.text

    def test_chunk_index_sequential(self, chunker, sample_text):
        """chunk_index metadata is 0, 1, 2, ..."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i

    def test_total_chunks_consistent(self, chunker, sample_text):
        """All chunks report the same total_chunks value."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        expected = len(chunks)
        for chunk in chunks:
            assert chunk.metadata["total_chunks"] == expected

    def test_two_comments_creates_two_chunks(self, chunker):
        """2 comments → 2 chunks."""
        text = _build_reddit_text(comments=[
            {"author": "UserA", "text": "This is a great discussion about NBA centers", "upvotes": 50},
            {"author": "UserB", "text": "I agree completely with the original poster here", "upvotes": 30},
        ])
        chunks = chunker.chunk_reddit_thread(text, "reddit.pdf")
        assert len(chunks) == 2
        assert chunks[0].metadata["comment_author"] == "UserA"
        assert chunks[1].metadata["comment_author"] == "UserB"

    def test_single_comment_creates_one_chunk(self, chunker):
        """1 comment → 1 chunk."""
        text = _build_reddit_text(comments=[
            {"author": "SingleUser", "text": "Great post about centers in the NBA", "upvotes": 100},
        ])
        chunks = chunker.chunk_reddit_thread(text, "reddit.pdf")
        assert len(chunks) == 1
        assert chunks[0].metadata["comment_author"] == "SingleUser"
        assert chunks[0].metadata["comment_upvotes"] == 100


# ---------------------------------------------------------------------------
# Tests: Post body extraction
# ---------------------------------------------------------------------------

class TestPostBodyExtraction:
    """Test post body extraction and inclusion in chunks."""

    def test_post_body_in_chunk_text(self, chunker, sample_text):
        """Post body text appears in the chunk."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        assert "Jokic and Embiid" in chunks[0].text

    def test_long_body_truncated(self, chunker):
        """Body longer than 300 chars is truncated with ellipsis."""
        long_body = "A" * 400
        text = _build_reddit_text(post_body=long_body, comments=[
            {"author": "TestUser", "text": "This is a comment about the NBA", "upvotes": 10},
        ])
        chunks = chunker.chunk_reddit_thread(text, "reddit.pdf")
        assert "..." in chunks[0].text
        # First 250 chars of the body should be present
        assert "A" * 100 in chunks[0].text


# ---------------------------------------------------------------------------
# Tests: Metadata fields
# ---------------------------------------------------------------------------

class TestChunkMetadata:
    """Test metadata fields on generated chunks."""

    REQUIRED_METADATA_KEYS = {
        "source", "type", "post_title", "post_author", "post_upvotes",
        "num_comments", "chunk_index", "total_chunks",
        "comment_author", "comment_upvotes", "is_nba_official",
    }

    def test_required_metadata_present(self, chunker, sample_text):
        """Every chunk has all required metadata fields."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            missing = self.REQUIRED_METADATA_KEYS - set(chunk.metadata.keys())
            assert not missing, f"Missing metadata keys: {missing}"

    def test_is_nba_official_is_int(self, chunker, sample_text):
        """is_nba_official stored as int (0/1), not bool."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            val = chunk.metadata["is_nba_official"]
            assert isinstance(val, int), f"Expected int, got {type(val)}"
            assert val in (0, 1)

    def test_nba_official_detected(self, chunker, sample_text):
        """Lakers is in NBA_OFFICIAL_ACCOUNTS, so exactly one chunk has is_nba_official=1."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        officials = [c for c in chunks if c.metadata["is_nba_official"] == 1]
        assert len(officials) == 1
        assert officials[0].metadata["comment_author"] == "Lakers"

    def test_comment_upvotes_is_numeric(self, chunker, sample_text):
        """comment_upvotes is a number > 0 for each chunk."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            upvotes = chunk.metadata["comment_upvotes"]
            assert isinstance(upvotes, int)
            assert upvotes > 0

    def test_type_is_reddit_thread(self, chunker, sample_text):
        """type metadata is 'reddit_thread'."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            assert chunk.metadata["type"] == "reddit_thread"


# ---------------------------------------------------------------------------
# Tests: No comments / edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and fallback behavior."""

    def test_no_comments_returns_single_chunk(self, chunker):
        """Thread with no extractable comments returns 1 basic chunk."""
        text = "r/nba\nSome title\nil y a 1 heure\nAuthor123\nSome title\nBody text here.\n50\n10\nPartager\n"
        chunks = chunker.chunk_reddit_thread(text, "reddit.pdf")
        assert len(chunks) == 1
        assert chunks[0].metadata["num_comments"] == 0
        assert chunks[0].metadata["comment_author"] == ""
        assert chunks[0].metadata["comment_upvotes"] == 0
        assert chunks[0].metadata["is_nba_official"] == 0

    def test_ad_filtering_removes_sponsored(self, chunker):
        """Sponsored content is filtered before chunking."""
        text = _build_reddit_text()
        text += "Sponsoris(e) Some ad content here\n\n"
        chunks = chunker.chunk_reddit_thread(text, "reddit.pdf")
        for chunk in chunks:
            assert "Sponsoris" not in chunk.text

    def test_unique_chunk_ids(self, chunker, sample_text):
        """All chunks from the same thread have unique IDs."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_each_chunk_has_one_comment_in_text(self, chunker, sample_text):
        """Each chunk text contains exactly one comment section."""
        chunks = chunker.chunk_reddit_thread(sample_text, "reddit.pdf")
        for chunk in chunks:
            # Count "=== COMMENT" occurrences (should be 1 per chunk)
            comment_sections = chunk.text.count("=== COMMENT")
            assert comment_sections == 1
