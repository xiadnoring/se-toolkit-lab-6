"""Regression tests for agent.py CLI."""

import json
import subprocess
import sys
from pathlib import Path


def test_agent_output_contains_answer_and_tool_calls() -> None:
    """Test that agent.py outputs valid JSON with answer and tool_calls fields."""
    project_root = Path(__file__).parent.parent.parent.parent
    agent_path = project_root / "agent.py"

    result = subprocess.run(
        [sys.executable, str(agent_path), "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"agent.py failed with: {result.stderr}"

    output = result.stdout.strip()
    assert output, "agent.py produced no stdout"

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(f"agent.py output is not valid JSON: {e}\nOutput: {output}") from e

    assert "answer" in data, "Missing 'answer' field in JSON output"
    assert "tool_calls" in data, "Missing 'tool_calls' field in JSON output"
    assert isinstance(data["tool_calls"], list), "'tool_calls' must be a list"
