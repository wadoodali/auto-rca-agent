from types import SimpleNamespace
from src.tools.openai_tool_adapter import create_tool_result

def test_create_tool_result_formats_function_output() -> None:
    """Verify that a tool result is formatted for the OpenAI Responses API."""

    tool_call = SimpleNamespace(call_id="call_test_123",)
    result = [{"source_type": "log", "incident_id": "INC-2026-001", "source_id": "log-001", "content": "Database connection pool reached 100%.","distance": 0.12,}]
    formatted = create_tool_result(tool_call=tool_call, result=result,)

    assert formatted["type"] == "function_call_output"
    assert formatted["call_id"] == "call_test_123"
    assert "Database connection pool reached 100%." in formatted["output"]