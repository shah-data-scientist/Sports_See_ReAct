"""
Unit tests for NBAToolkit and tool wrappers
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.agents.tools import NBAToolkit, create_nba_tools
from src.models.document import DocumentChunk


class TestNBAToolkit:
    """Test NBAToolkit tool wrappers."""

    def test_query_nba_database_success(self):
        """Test SQL tool wrapper with successful query."""
        mock_sql_tool = Mock()
        mock_sql_tool.query.return_value = {
            "sql": "SELECT * FROM players",
            "results": [{"name": "Player1", "pts": 100}],
            "error": None,
        }

        toolkit = NBAToolkit(
            sql_tool=mock_sql_tool,
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=Mock(),
        )

        result = toolkit.query_nba_database("Who scored the most?")

        assert result["row_count"] == 1
        assert result["error"] is None
        assert len(result["results"]) == 1
        assert result["sql"] == "SELECT * FROM players"

    def test_query_nba_database_error(self):
        """Test SQL tool wrapper with error."""
        mock_sql_tool = Mock()
        mock_sql_tool.query.return_value = {
            "sql": "",
            "results": [],
            "error": "Syntax error",
        }

        toolkit = NBAToolkit(
            sql_tool=mock_sql_tool,
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=Mock(),
        )

        result = toolkit.query_nba_database("Invalid query")

        assert result["row_count"] == 0
        assert result["error"] == "Syntax error"

    def test_query_nba_database_exception(self):
        """Test SQL tool wrapper handles exceptions."""
        mock_sql_tool = Mock()
        mock_sql_tool.query.side_effect = Exception("Database connection failed")

        toolkit = NBAToolkit(
            sql_tool=mock_sql_tool,
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=Mock(),
        )

        result = toolkit.query_nba_database("Test query")

        assert result["row_count"] == 0
        assert "Database connection failed" in result["error"]

    def test_search_knowledge_base_success(self):
        """Test vector search wrapper with successful results."""
        # Create mock chunks
        chunk1 = DocumentChunk(
            id="chunk-1",
            text="Lakers are a great team with rich history",
            metadata={"source": "reddit", "title": "Lakers discussion", "upvotes": 100},
        )
        chunk2 = DocumentChunk(
            id="chunk-2",
            text="LeBron James is one of the all-time greats",
            metadata={"source": "nba.com", "author": "ESPN", "upvotes": 50},
        )

        mock_vector_store = Mock()
        mock_vector_store.search.return_value = [
            (chunk1, 0.95),
            (chunk2, 0.85),
        ]

        mock_embedding_service = Mock()
        mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            visualization_service=Mock(),
        )

        result = toolkit.search_knowledge_base("Lakers history", k=5)

        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert "reddit" in result["sources"]
        assert "nba.com" in result["sources"]
        assert result["results"][0]["score"] == 0.95
        assert "Lakers" in result["results"][0]["text"]

    def test_search_knowledge_base_no_results(self):
        """Test vector search with no results."""
        mock_vector_store = Mock()
        mock_vector_store.search.return_value = []

        mock_embedding_service = Mock()
        mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            visualization_service=Mock(),
        )

        result = toolkit.search_knowledge_base("Obscure query")

        assert result["count"] == 0
        assert len(result["results"]) == 0
        assert len(result["sources"]) == 0

    def test_search_knowledge_base_exception(self):
        """Test vector search handles exceptions."""
        mock_embedding_service = Mock()
        mock_embedding_service.embed_query.side_effect = Exception("Embedding failed")

        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=Mock(),
            embedding_service=mock_embedding_service,
            visualization_service=Mock(),
        )

        result = toolkit.search_knowledge_base("Test query")

        assert result["count"] == 0
        assert "Embedding failed" in result["error"]

    def test_create_visualization_success(self):
        """Test visualization creation with valid SQL results."""
        mock_viz_service = Mock()
        mock_viz_service.generate_visualization.return_value = {
            "plotly_json": '{"data": [], "layout": {}}',
            "chart_type": "bar",
        }

        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=mock_viz_service,
        )

        sql_results = [
            {"name": "Player1", "pts": 100},
            {"name": "Player2", "pts": 90},
        ]

        result = toolkit.create_visualization("Top scorers", sql_results)

        assert result["error"] is None
        assert result["chart_type"] == "bar"
        assert result["plotly_json"] is not None

    def test_create_visualization_empty_results(self):
        """Test visualization with empty SQL results."""
        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=Mock(),
        )

        result = toolkit.create_visualization("Query", [])

        assert result["error"] == "No data to visualize"
        assert result["plotly_json"] is None

    def test_create_visualization_exception(self):
        """Test visualization handles exceptions."""
        mock_viz_service = Mock()
        mock_viz_service.generate_visualization.side_effect = Exception("Viz error")

        toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=mock_viz_service,
        )

        result = toolkit.create_visualization("Query", [{"data": "test"}])

        assert "Viz error" in result["error"]


class TestCreateNBATools:
    """Test tool factory function."""

    def test_create_nba_tools(self):
        """Test creating tools from toolkit."""
        mock_toolkit = NBAToolkit(
            sql_tool=Mock(),
            vector_store=Mock(),
            embedding_service=Mock(),
            visualization_service=Mock(),
        )

        tools = create_nba_tools(mock_toolkit)

        assert len(tools) == 3

        # Check tool names
        tool_names = [t.name for t in tools]
        assert "query_nba_database" in tool_names
        assert "search_knowledge_base" in tool_names
        assert "create_visualization" in tool_names

        # Check tools have required attributes
        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.function
            assert tool.parameters
            assert isinstance(tool.examples, list)

    def test_tool_functions_callable(self):
        """Test that tool functions are callable."""
        mock_toolkit = Mock()
        mock_toolkit.query_nba_database = Mock(return_value={"results": []})
        mock_toolkit.search_knowledge_base = Mock(return_value={"results": []})
        mock_toolkit.create_visualization = Mock(return_value={"error": None})

        tools = create_nba_tools(mock_toolkit)

        # Test each tool can be called
        for tool in tools:
            assert callable(tool.function)
