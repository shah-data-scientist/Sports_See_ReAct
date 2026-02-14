"""
Unit tests for ReAct agent
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.agents.react_agent import ReActAgent, Tool, AgentStep


class MockLLMClient:
    """Mock Google Generative AI client for testing."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
        self.models = Mock()
        self.models.generate_content = self._generate_content

    def _generate_content(self, **kwargs):
        response = Mock()
        if self.call_count < len(self.responses):
            response.text = self.responses[self.call_count]
        else:
            response.text = "Final Answer: No more mock responses"
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
            max_iterations=3,
        )

        assert len(agent.tools) == 1
        assert "test_tool" in agent.tools
        assert agent.max_iterations == 3

    def test_agent_returns_final_answer(self):
        """Test agent recognizes Final Answer and stops."""
        mock_client = MockLLMClient([
            "Thought: I can answer this\nFinal Answer: The answer is 42"
        ])

        tool = Tool(
            name="dummy_tool",
            description="Dummy",
            function=lambda: "dummy",
            parameters={},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)
        result = agent.run("What is the answer?")

        assert "The answer is 42" in result["answer"]
        assert result["total_steps"] == 0  # No tools executed
        assert not result["max_iterations_reached"]

    def test_agent_executes_tool(self):
        """Test agent executes tool and includes in trace."""
        # Mock responses: 1) Action, 2) Final Answer
        mock_client = MockLLMClient([
            'Thought: Need to query\nAction: query_tool\nAction Input: {"question": "test"}',
            "Thought: Got results\nFinal Answer: The result is X"
        ])

        mock_function = Mock(return_value={"results": [{"value": "X"}], "row_count": 1})
        tool = Tool(
            name="query_tool",
            description="Query tool",
            function=mock_function,
            parameters={"question": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)
        result = agent.run("test question")

        assert mock_function.called
        assert result["total_steps"] == 1
        assert "query_tool" in result["tools_used"]
        assert len(result["reasoning_trace"]) == 1

    def test_agent_handles_unknown_tool(self):
        """Test agent handles unknown tool gracefully."""
        mock_client = MockLLMClient([
            'Thought: Try unknown\nAction: unknown_tool\nAction Input: {"x": "y"}',
            "Final Answer: Could not complete"
        ])

        tool = Tool(
            name="real_tool",
            description="Real",
            function=lambda: "result",
            parameters={},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)
        result = agent.run("test")

        # Should have error observation
        assert result["total_steps"] == 1
        assert "ERROR" in result["reasoning_trace"][0]["observation"]

    def test_agent_stops_at_max_iterations(self):
        """Test agent stops after max iterations."""
        # Return actions indefinitely (no Final Answer)
        mock_client = MockLLMClient([
            'Thought: Step 1\nAction: tool1\nAction Input: {"q": "1"}',
            'Thought: Step 2\nAction: tool1\nAction Input: {"q": "2"}',
            'Thought: Step 3\nAction: tool1\nAction Input: {"q": "3"}',
        ])

        tool = Tool(
            name="tool1",
            description="Tool",
            function=lambda q: f"Result {q}",
            parameters={"q": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client, max_iterations=3)
        result = agent.run("test")

        assert result["max_iterations_reached"]
        assert result["total_steps"] == 3

    def test_agent_detects_repeated_actions(self):
        """Test agent detects infinite loops."""
        # Same action 3 times
        mock_client = MockLLMClient([
            'Thought: Try 1\nAction: tool1\nAction Input: {"x": "same"}',
            'Thought: Try 2\nAction: tool1\nAction Input: {"x": "same"}',
            'Thought: Try 3\nAction: tool1\nAction Input: {"x": "same"}',
        ])

        tool = Tool(
            name="tool1",
            description="Tool",
            function=lambda x: "result",
            parameters={"x": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client, max_iterations=5)
        result = agent.run("test")

        # Should stop before max iterations due to repetition
        assert result["total_steps"] == 3
        assert "repeated actions" in result["stop_reason"].lower()

    def test_parse_response_final_answer(self):
        """Test parsing Final Answer format."""
        mock_client = MockLLMClient([])
        agent = ReActAgent(tools=[], llm_client=mock_client)

        response = "Thought: Done\nFinal Answer: The answer is 42"
        parsed = agent._parse_response(response)

        assert parsed["type"] == "final_answer"
        assert "42" in parsed["answer"]

    def test_parse_response_action(self):
        """Test parsing Action format."""
        mock_client = MockLLMClient([])
        agent = ReActAgent(tools=[], llm_client=mock_client)

        response = (
            'Thought: Need data\n'
            'Action: query_tool\n'
            'Action Input: {"question": "test query"}'
        )
        parsed = agent._parse_response(response)

        assert parsed["type"] == "action"
        assert parsed["thought"] == "Need data"
        assert parsed["action"] == "query_tool"
        assert parsed["action_input"]["question"] == "test query"

    def test_tool_execution_error_handling(self):
        """Test tool execution handles errors gracefully."""
        mock_client = MockLLMClient([])

        def failing_tool(x):
            raise ValueError("Tool failed")

        tool = Tool(
            name="failing_tool",
            description="Fails",
            function=failing_tool,
            parameters={"x": "str"},
        )

        agent = ReActAgent(tools=[tool], llm_client=mock_client)
        observation = agent._execute_tool("failing_tool", {"x": "test"})

        assert "ERROR" in observation
        assert "Tool failed" in observation

    def test_format_observation_sql_results(self):
        """Test SQL results formatting."""
        mock_client = MockLLMClient([])
        agent = ReActAgent(tools=[], llm_client=mock_client)

        result = {
            "results": [
                {"name": "Player1", "pts": 100},
                {"name": "Player2", "pts": 90},
            ],
            "row_count": 2,
        }

        observation = agent._format_observation(result)

        assert "SQL Results" in observation
        assert "Player1" in observation
        assert "100" in observation

    def test_format_observation_vector_results(self):
        """Test vector search results formatting."""
        mock_client = MockLLMClient([])
        agent = ReActAgent(tools=[], llm_client=mock_client)

        result = {
            "results": [
                {"text": "Document 1 content", "score": 0.95, "source": "reddit"},
                {"text": "Document 2 content", "score": 0.85, "source": "nba.com"},
            ],
            "sources": ["reddit", "nba.com"],
            "count": 2,
        }

        observation = agent._format_observation(result)

        assert "Found 2 documents" in observation
        assert "reddit" in observation
        assert "Document 1" in observation


class TestAgentStep:
    """Test AgentStep dataclass."""

    def test_agent_step_creation(self):
        """Test creating an agent step."""
        step = AgentStep(
            thought="I need data",
            action="query_tool",
            action_input={"question": "test"},
            observation="Results: [...]",
            step_number=1,
        )

        assert step.thought == "I need data"
        assert step.action == "query_tool"
        assert step.step_number == 1


class TestTool:
    """Test Tool dataclass."""

    def test_tool_creation(self):
        """Test creating a tool."""

        def my_func(x: str) -> str:
            return f"Result: {x}"

        tool = Tool(
            name="my_tool",
            description="My test tool",
            function=my_func,
            parameters={"x": "str"},
            examples=["example 1", "example 2"],
        )

        assert tool.name == "my_tool"
        assert tool.function("test") == "Result: test"
        assert len(tool.examples) == 2
