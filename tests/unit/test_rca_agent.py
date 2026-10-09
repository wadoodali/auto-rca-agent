import json
from types import SimpleNamespace

import pytest

from src.agent import rca_agent
from src.schemas.incident import IncidentReport


def tool_call(
    name: str,
    arguments: str,
    call_id: str = "call_test",
) -> SimpleNamespace:
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=arguments,
        call_id=call_id,
    )


def test_unique_tool_call_executes() -> None:
    seen: set[tuple[str, str]] = set()
    calls = [tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')]
    executed: list[str] = []

    def fake_run_tool_call(call: SimpleNamespace) -> list[dict[str, str]]:
        executed.append(call.name)
        return [{"result": "ok"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        results = rca_agent.execute_requested_tools(calls, seen, "INC-1")
    finally:
        rca_agent.run_tool_call = original

    assert executed == ["query_git_commits"]
    assert results[0][1] == [{"result": "ok"}]


def test_mismatched_incident_id_is_rejected_before_backend_execution() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call(
        "query_git_commits",
        '{"incident_id":"INC-2026-002","query":"pool"}',
    )
    executed = False

    def fake_run_tool_call(_: SimpleNamespace) -> list[dict[str, str]]:
        nonlocal executed
        executed = True
        return [{"result": "unexpected"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        results = rca_agent.execute_requested_tools(
            [call],
            seen,
            "INC-2026-001",
        )
    finally:
        rca_agent.run_tool_call = original

    assert executed is False
    assert results[0][1] == [{
        "error": (
            "Tool call incident_id does not match "
            "the investigation incident."
        ),
        "tool_name": "query_git_commits",
    }]


def test_mismatched_incident_preserves_output_and_trace() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call(
        "query_git_commits",
        '{"incident_id":"INC-2026-002","query":"pool"}',
        call_id="call_mismatch",
    )

    results = rca_agent.execute_requested_tools(
        [call],
        seen,
        "INC-2026-001",
    )
    formatted = rca_agent.format_tool_results(results)
    trace = rca_agent.build_execution_trace(results, [1])

    assert formatted[0]["type"] == "function_call_output"
    assert formatted[0]["call_id"] == "call_mismatch"
    assert json.loads(formatted[0]["output"])[0]["error"] == (
        "Tool call incident_id does not match the investigation incident."
    )
    assert trace[0]["status"] == "error"
    assert trace[0]["result_count"] == 0


def test_future_matching_incident_id_remains_supported() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call(
        "query_git_commits",
        '{"incident_id":"INC-2027-001","query":"pool"}',
    )
    executed: list[str] = []

    def fake_run_tool_call(tool_call: SimpleNamespace) -> list[dict[str, str]]:
        executed.append(tool_call.name)
        return [{"result": "ok"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        results = rca_agent.execute_requested_tools(
            [call],
            seen,
            "INC-2027-001",
        )
    finally:
        rca_agent.run_tool_call = original

    assert executed == ["query_git_commits"]
    assert results[0][1] == [{"result": "ok"}]


@pytest.mark.parametrize(
    "arguments",
    [
        '{"incident_id":"INC-2026-002","query":"pool","extra":"value"}',
        '{"query":"pool"}',
        '{"incident_id":"INC-2026-002"}',
        '{"incident_id":123,"query":"pool"}',
        '{"incident_id":"INC-2026-002","query":123}',
        '{"incident_id":"INC-2026-002","query":"pool"',
    ],
)
def test_invalid_arguments_reach_existing_executor_validation(
    arguments: str,
) -> None:
    call = tool_call("query_git_commits", arguments)

    results = rca_agent.execute_requested_tools(
        [call],
        set(),
        "INC-2026-001",
    )

    assert results[0][1][0]["error"] == (
        "Tool 'query_git_commits' could not be executed."
    )


def test_successful_trace_includes_existing_fields_and_observability() -> None:
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')
    trace = rca_agent.build_execution_trace(
        [(call, [{"evidence": "found"}])],
        [3],
    )

    assert trace == [{
        "tool_name": "query_git_commits",
        "tool_call": call.arguments,
        "result": [{"evidence": "found"}],
        "round": 3,
        "status": "success",
        "result_count": 1,
    }]


def test_empty_successful_trace_has_empty_status_and_zero_count() -> None:
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')

    trace = rca_agent.build_execution_trace([(call, [])], [1])

    assert trace[0]["status"] == "empty"
    assert trace[0]["result_count"] == 0


def test_tool_failure_trace_has_error_status_and_zero_count() -> None:
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')

    trace = rca_agent.build_execution_trace(
        [(call, [{"error": "Tool failed", "tool_name": call.name}])],
        [1],
    )

    assert trace[0]["status"] == "error"
    assert trace[0]["result_count"] == 0


def test_duplicate_trace_has_duplicate_status_and_zero_count() -> None:
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')

    trace = rca_agent.build_execution_trace(
        [(
            call,
            [{
                "error": "Exact duplicate tool call was not executed.",
                "tool_name": call.name,
            }],
        )],
        [2],
    )

    assert trace[0]["status"] == "duplicate"
    assert trace[0]["result_count"] == 0


def test_trace_preserves_round_numbers_for_calls_in_different_rounds() -> None:
    first_call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')
    second_call = tool_call("fetch_incident_logs", '{"incident_id":"INC-1","query":"errors"}')

    trace = rca_agent.build_execution_trace(
        [
            (first_call, [{"evidence": "commit"}]),
            (second_call, [{"evidence": "log"}]),
        ],
        [1, 2],
    )

    assert [item["round"] for item in trace] == [1, 2]


def test_enriched_trace_is_compatible_with_investigation_result() -> None:
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')
    trace = rca_agent.build_execution_trace(
        [(call, [{"evidence": "found"}])],
        [1],
    )
    report = IncidentReport(
        likely_cause="Test cause",
        evidence=["Test evidence"],
        confidence=0.9,
        suggested_remediation="Test remediation",
    )

    result = rca_agent.InvestigationResult(
        report=report,
        execution_trace=trace,
    )

    assert result.execution_trace == trace


def test_exact_duplicate_does_not_execute_twice_and_returns_error() -> None:
    seen: set[tuple[str, str]] = set()
    calls = [
        tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}'),
        tool_call("query_git_commits", '{"query":"pool","incident_id":"INC-1"}'),
    ]
    execution_count = 0

    def fake_run_tool_call(call: SimpleNamespace) -> list[dict[str, str]]:
        nonlocal execution_count
        execution_count += 1
        return [{"result": "ok"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        results = rca_agent.execute_requested_tools(calls, seen, "INC-1")
    finally:
        rca_agent.run_tool_call = original

    assert execution_count == 1
    assert results[1][1] == [{
        "error": "Exact duplicate tool call was not executed.",
        "tool_name": "query_git_commits",
    }]


def test_different_arguments_and_tools_remain_allowed() -> None:
    seen: set[tuple[str, str]] = set()
    calls = [
        tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}'),
        tool_call("query_git_commits", '{"incident_id":"INC-1","query":"leak"}'),
        tool_call("fetch_incident_logs", '{"incident_id":"INC-1","query":"pool"}'),
    ]
    executed: list[str] = []

    def fake_run_tool_call(call: SimpleNamespace) -> list[dict[str, str]]:
        executed.append(call.name + call.arguments)
        return [{"result": "ok"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        results = rca_agent.execute_requested_tools(calls, seen, "INC-1")
    finally:
        rca_agent.run_tool_call = original

    assert len(executed) == 3
    assert all(result == [{"result": "ok"}] for _, result in results)


def test_duplicate_across_investigation_rounds_is_detected() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')
    execution_count = 0

    def fake_run_tool_call(tool_call: SimpleNamespace) -> list[dict[str, str]]:
        nonlocal execution_count
        execution_count += 1
        return [{"result": "ok"}]

    original = rca_agent.run_tool_call
    rca_agent.run_tool_call = fake_run_tool_call
    try:
        first = rca_agent.execute_requested_tools([call], seen, "INC-1")
        second = rca_agent.execute_requested_tools([call], seen, "INC-1")
    finally:
        rca_agent.run_tool_call = original

    assert execution_count == 1
    assert first[0][1] == [{"result": "ok"}]
    assert second[0][1][0]["error"] == "Exact duplicate tool call was not executed."


def test_separate_investigations_have_independent_duplicate_state(monkeypatch) -> None:
    report = IncidentReport(
        likely_cause="Test cause",
        evidence=["Test evidence"],
        confidence=0.9,
        suggested_remediation="Test remediation",
    )
    call = tool_call("query_git_commits", '{"incident_id":"INC-1","query":"pool"}')
    responses = iter([
        SimpleNamespace(output=[call], output_parsed=None),
        SimpleNamespace(output=[], output_parsed=report),
        SimpleNamespace(output=[call], output_parsed=None),
        SimpleNamespace(output=[], output_parsed=report),
    ])
    execution_count = 0

    monkeypatch.setattr(rca_agent, "request_investigation", lambda **_: next(responses))
    monkeypatch.setattr(rca_agent, "continue_investigation", lambda **_: next(responses))

    def fake_run_tool_call(tool_call: SimpleNamespace) -> list[dict[str, str]]:
        nonlocal execution_count
        execution_count += 1
        return [{"result": "ok"}]

    monkeypatch.setattr(rca_agent, "run_tool_call", fake_run_tool_call)

    rca_agent.run_investigation("INC-1", "investigate")
    rca_agent.run_investigation("INC-1", "investigate")

    assert execution_count == 2


def test_duplicate_preserves_call_id_and_function_call_output() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call(
        "query_git_commits",
        '{"incident_id":"INC-1","query":"pool"}',
        call_id="call_duplicate",
    )
    rca_agent.execute_requested_tools([call], seen, "INC-1")
    duplicate_result = rca_agent.execute_requested_tools([call], seen, "INC-1")

    formatted = rca_agent.format_tool_results(duplicate_result)

    assert formatted[0]["type"] == "function_call_output"
    assert formatted[0]["call_id"] == "call_duplicate"
    assert json.loads(formatted[0]["output"])[0]["error"] == (
        "Exact duplicate tool call was not executed."
    )


def test_duplicate_appears_in_existing_execution_trace() -> None:
    seen: set[tuple[str, str]] = set()
    call = tool_call(
        "query_git_commits",
        '{"incident_id":"INC-1","query":"pool"}',
    )
    rca_agent.execute_requested_tools([call], seen, "INC-1")
    duplicate_results = rca_agent.execute_requested_tools([call], seen, "INC-1")

    trace = rca_agent.build_execution_trace(duplicate_results)

    assert trace[0]["tool_name"] == "query_git_commits"
    assert trace[0]["result"][0]["error"] == (
        "Exact duplicate tool call was not executed."
    )
