from collections.abc import Callable
from typing import Any
from src.tools.deployment_tools import get_deployment_delta
from src.tools.git_tools import query_git_commits
from src.tools.log_tools import fetch_incident_logs
from src.tools.tool_definitions import (DEPLOYMENT_TOOL, GIT_COMMITS_TOOL, INCIDENT_LOGS_TOOL,)

ToolFunction = Callable[..., list[dict[str, Any]]]

TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "query_git_commits": query_git_commits,
    "fetch_incident_logs": fetch_incident_logs,
    "get_deployment_delta": get_deployment_delta,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [GIT_COMMITS_TOOL, INCIDENT_LOGS_TOOL, DEPLOYMENT_TOOL,]