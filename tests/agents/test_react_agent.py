"""
Unit tests for ReAct agent (refactored version)
Tests the classification-based, single-pass agent architecture.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.agents.react_agent import ReActAgent, Tool


class MockLLMClient:
    """Mock Google Generative AI client for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.call_count = 0
        self.models = Mock()
        self.models.generate_content = self._generate_content

    def _generate_content(self, **kwargs):
        response = Mock()
        if self.call_count < len(self.responses):
            response.text = self.responses[self.call_count]
        else:
            response.text = "Default response"
        self.call_count += 1
        return response


class TestReActAgent:
    """Test ReAct agent functionality."""

    def test_agent_initialization(self):
        """Test agent initializes with tools."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=lambda x: "result",
            parameters={"param": "str"},
        )

        agent = ReActAgent(
            tools=[tool],
            llm_client=mock_client,
        )

        assert len(agent.tools) == 1
        assert "test_tool" in agent.tools
        assert agent.model == "gemini-2.0-flash"
        assert agent.temperature == 0.1

    def test_agent_with_custom_model(self):
        """Test agent accepts custom model and temperature."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=lambda x: "result",
            parameters={"param": "str"},
        )

        agent = ReActAgent(
            tools=[tool],
            llm_client=mock_client,
            model="custom-model",
            temperature=0.5,
        )

        assert agent.model == "custom-model"
        assert agent.temperature == 0.5

    @patch('src.agents.react_agent.QueryClassifier')
    def test_agent_creates_classifier(self, mock_classifier_class):
        """Test agent creates a QueryClassifier instance."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=lambda x: "result",
            parameters={"param": "str"},
        )

        agent = ReActAgent(
            tools=[tool],
            llm_client=mock_client,
            model="test-model",
        )

        # Verify QueryClassifier was instantiated with correct params
        mock_classifier_class.assert_called_once_with(
            client=mock_client,
            model="test-model"
        )

    def test_tool_storage(self):
        """Test tools are stored in a dict by name."""
        mock_client = MockLLMClient([])
        tools = [
            Tool(
                name="tool1",
                description="First tool",
                function=lambda x: "result1",
                parameters={"p1": "str"},
            ),
            Tool(
                name="tool2",
                description="Second tool",
                function=lambda x: "result2",
                parameters={"p2": "str"},
            ),
        ]

        agent = ReActAgent(tools=tools, llm_client=mock_client)

        assert len(agent.tools) == 2
        assert "tool1" in agent.tools
        assert "tool2" in agent.tools
        assert agent.tools["tool1"].description == "First tool"
        assert agent.tools["tool2"].description == "Second tool"

    @patch('src.agents.react_agent.QueryClassifier')
    def test_run_method_exists(self, mock_classifier_class):
        """Test agent has run method."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=lambda x: {"result": "data"},
            parameters={"query": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)

        assert hasattr(agent, 'run')
        assert callable(agent.run)

    def test_tool_with_examples(self):
        """Test tool can have examples."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool with examples",
            function=lambda x: "result",
            parameters={"param": "str"},
            examples=["Example 1", "Example 2"],
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)

        assert len(agent.tools["test_tool"].examples) == 2
        assert "Example 1" in agent.tools["test_tool"].examples

    def test_multiple_tools_initialization(self):
        """Test agent can handle multiple tools with different signatures."""
        mock_client = MockLLMClient([])
        tools = [
            Tool(
                name="query_database",
                description="Query NBA database",
                function=lambda query: {"results": []},
                parameters={"query": "str"},
            ),
            Tool(
                name="search_knowledge",
                description="Search knowledge base",
                function=lambda query, top_k: {"documents": []},
                parameters={"query": "str", "top_k": "int"},
            ),
        ]

        agent = ReActAgent(tools=tools, llm_client=mock_client)

        assert len(agent.tools) == 2
        assert agent.tools["query_database"].function("test")["results"] == []
        assert "documents" in agent.tools["search_knowledge"].function("test", 5)

    @patch('src.agents.react_agent.QueryClassifier')
    def test_agent_stores_tool_results(self, mock_classifier_class):
        """Test agent has tool_results storage."""
        mock_client = MockLLMClient([])
        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=lambda x: "result",
            parameters={"param": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)

        assert hasattr(agent, 'tool_results')
        assert isinstance(agent.tool_results, dict)
