"""
FILE: test_feedback.py
STATUS: Active
RESPONSIBILITY: Tests for feedback Pydantic models and enums
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models.feedback import (
    ChatInteractionCreate,
    ChatInteractionResponse,
    FeedbackCreate,
    FeedbackRating,
    FeedbackResponse,
    FeedbackStats,
)


class TestFeedbackRating:
    """Tests for FeedbackRating enum."""

    def test_feedback_rating_values(self):
        """Test FeedbackRating enum has correct values."""
        assert FeedbackRating.POSITIVE.value == "positive"
        assert FeedbackRating.NEGATIVE.value == "negative"

    def test_feedback_rating_members(self):
        """Test FeedbackRating has exactly two members."""
        assert len(FeedbackRating) == 2
        assert set(FeedbackRating) == {FeedbackRating.POSITIVE, FeedbackRating.NEGATIVE}


class TestChatInteractionCreate:
    """Tests for ChatInteractionCreate Pydantic model."""

    def test_valid_chat_interaction_create(self):
        """Test creating a valid ChatInteractionCreate."""
        interaction = ChatInteractionCreate(
            query="What is LeBron's average?",
            response="LeBron averages 27.2 points per game.",
            sources=["nba_stats.xlsx"],
            processing_time_ms=1234,
            conversation_id="conv-123",
            turn_number=1,
        )
        assert interaction.query == "What is LeBron's average?"
        assert interaction.response == "LeBron averages 27.2 points per game."
        assert interaction.sources == ["nba_stats.xlsx"]
        assert interaction.processing_time_ms == 1234
        assert interaction.conversation_id == "conv-123"
        assert interaction.turn_number == 1

    def test_chat_interaction_create_minimal(self):
        """Test ChatInteractionCreate with minimal required fields."""
        interaction = ChatInteractionCreate(
            query="Test query",
            response="Test response",
        )
        assert interaction.query == "Test query"
        assert interaction.response == "Test response"
        assert interaction.sources == []  # Default empty list
        assert interaction.processing_time_ms is None
        assert interaction.conversation_id is None
        assert interaction.turn_number is None

    def test_chat_interaction_create_empty_query_fails(self):
        """Test ChatInteractionCreate fails with empty query."""
        with pytest.raises(ValidationError) as exc_info:
            ChatInteractionCreate(query="", response="Test response")
        assert "query" in str(exc_info.value)

    def test_chat_interaction_create_empty_response_fails(self):
        """Test ChatInteractionCreate fails with empty response."""
        with pytest.raises(ValidationError) as exc_info:
            ChatInteractionCreate(query="Test query", response="")
        assert "response" in str(exc_info.value)

    def test_chat_interaction_create_query_too_long_fails(self):
        """Test ChatInteractionCreate fails with query exceeding max_length."""
        long_query = "x" * 10001
        with pytest.raises(ValidationError) as exc_info:
            ChatInteractionCreate(query=long_query, response="Test response")
        assert "query" in str(exc_info.value)


class TestChatInteractionResponse:
    """Tests for ChatInteractionResponse Pydantic model."""

    def test_valid_chat_interaction_response(self):
        """Test creating a valid ChatInteractionResponse."""
        now = datetime.utcnow()
        interaction = ChatInteractionResponse(
            id="int-123",
            query="What is LeBron's average?",
            response="LeBron averages 27.2 points per game.",
            sources=["nba_stats.xlsx"],
            processing_time_ms=1234,
            created_at=now,
            conversation_id="conv-123",
            turn_number=1,
        )
        assert interaction.id == "int-123"
        assert interaction.query == "What is LeBron's average?"
        assert interaction.response == "LeBron averages 27.2 points per game."
        assert interaction.sources == ["nba_stats.xlsx"]
        assert interaction.processing_time_ms == 1234
        assert interaction.created_at == now
        assert interaction.conversation_id == "conv-123"
        assert interaction.turn_number == 1
        assert interaction.feedback is None

    def test_chat_interaction_response_with_feedback(self):
        """Test ChatInteractionResponse with associated feedback."""
        now = datetime.utcnow()
        feedback = FeedbackResponse(
            id=1,
            interaction_id="int-123",
            rating=FeedbackRating.POSITIVE,
            comment="Great answer!",
            created_at=now,
        )
        interaction = ChatInteractionResponse(
            id="int-123",
            query="Test query",
            response="Test response",
            sources=[],
            processing_time_ms=100,
            created_at=now,
            feedback=feedback,
        )
        assert interaction.feedback is not None
        assert interaction.feedback.rating == FeedbackRating.POSITIVE
        assert interaction.feedback.comment == "Great answer!"


class TestFeedbackCreate:
    """Tests for FeedbackCreate Pydantic model."""

    def test_valid_feedback_create(self):
        """Test creating a valid FeedbackCreate."""
        feedback = FeedbackCreate(
            interaction_id="int-123",
            rating=FeedbackRating.POSITIVE,
            comment="Excellent response!",
        )
        assert feedback.interaction_id == "int-123"
        assert feedback.rating == FeedbackRating.POSITIVE
        assert feedback.comment == "Excellent response!"

    def test_feedback_create_without_comment(self):
        """Test FeedbackCreate without optional comment."""
        feedback = FeedbackCreate(
            interaction_id="int-123",
            rating=FeedbackRating.NEGATIVE,
        )
        assert feedback.interaction_id == "int-123"
        assert feedback.rating == FeedbackRating.NEGATIVE
        assert feedback.comment is None

    def test_feedback_create_comment_too_long_fails(self):
        """Test FeedbackCreate fails with comment exceeding max_length."""
        long_comment = "x" * 2001
        with pytest.raises(ValidationError) as exc_info:
            FeedbackCreate(
                interaction_id="int-123",
                rating=FeedbackRating.NEGATIVE,
                comment=long_comment,
            )
        assert "comment" in str(exc_info.value)

    def test_feedback_create_missing_required_fields_fails(self):
        """Test FeedbackCreate fails without required fields."""
        with pytest.raises(ValidationError):
            FeedbackCreate(interaction_id="int-123")  # Missing rating

        with pytest.raises(ValidationError):
            FeedbackCreate(rating=FeedbackRating.POSITIVE)  # Missing interaction_id


class TestFeedbackResponse:
    """Tests for FeedbackResponse Pydantic model."""

    def test_valid_feedback_response(self):
        """Test creating a valid FeedbackResponse."""
        now = datetime.utcnow()
        feedback = FeedbackResponse(
            id=1,
            interaction_id="int-123",
            rating=FeedbackRating.POSITIVE,
            comment="Great!",
            created_at=now,
        )
        assert feedback.id == 1
        assert feedback.interaction_id == "int-123"
        assert feedback.rating == FeedbackRating.POSITIVE
        assert feedback.comment == "Great!"
        assert feedback.created_at == now

    def test_feedback_response_without_comment(self):
        """Test FeedbackResponse with null comment."""
        now = datetime.utcnow()
        feedback = FeedbackResponse(
            id=2,
            interaction_id="int-456",
            rating=FeedbackRating.NEGATIVE,
            comment=None,
            created_at=now,
        )
        assert feedback.id == 2
        assert feedback.comment is None


class TestFeedbackStats:
    """Tests for FeedbackStats Pydantic model."""

    def test_valid_feedback_stats(self):
        """Test creating valid FeedbackStats."""
        stats = FeedbackStats(
            total_interactions=100,
            total_feedback=75,
            positive_count=60,
            negative_count=15,
            feedback_rate=75.0,
            positive_rate=80.0,
        )
        assert stats.total_interactions == 100
        assert stats.total_feedback == 75
        assert stats.positive_count == 60
        assert stats.negative_count == 15
        assert stats.feedback_rate == 75.0
        assert stats.positive_rate == 80.0

    def test_feedback_stats_zero_values(self):
        """Test FeedbackStats with zero values."""
        stats = FeedbackStats(
            total_interactions=0,
            total_feedback=0,
            positive_count=0,
            negative_count=0,
            feedback_rate=0.0,
            positive_rate=0.0,
        )
        assert stats.total_interactions == 0
        assert stats.total_feedback == 0
        assert stats.feedback_rate == 0.0
        assert stats.positive_rate == 0.0

    def test_feedback_stats_all_negative(self):
        """Test FeedbackStats with all negative feedback."""
        stats = FeedbackStats(
            total_interactions=50,
            total_feedback=20,
            positive_count=0,
            negative_count=20,
            feedback_rate=40.0,
            positive_rate=0.0,
        )
        assert stats.positive_count == 0
        assert stats.negative_count == 20
        assert stats.positive_rate == 0.0
