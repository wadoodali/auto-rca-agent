from src.llm.client import create_openai_client
from src.tools.tool_registry import TOOL_SCHEMAS
from src.tools.openai_tool_adapter import create_tool_result, run_tool_call

def main() -> None:
    """Verify that an LLM tool call can be executed by the tool runner."""

    client = create_openai_client()
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=(
            "Investigate incident INC-2026-001. "
            "Find evidence about database connection pool exhaustion "
            "and connection timeouts. Use the available tools to retrieve "
            "the relevant evidence."
        ),
        tools=TOOL_SCHEMAS,
    )

    tool_calls = [
        item
        for item in response.output
        if item.type == "function_call"
    ]

    if not tool_calls:
        raise RuntimeError("The model did not request any tool calls.")

    for tool_call in tool_calls:
        print(f"Tool requested: {tool_call.name}")

        results = run_tool_call(tool_call)

        tool_result = create_tool_result(
            tool_call=tool_call,
            result=results,
        )

        print(f"Result call ID: {tool_result['call_id']}")
        print(f"Result type: {tool_result['type']}")
        print(f"Result contains: {len(tool_result['output'])} characters")

if __name__ == "__main__":
    main()