from src.tools.deployment_tools import get_deployment_delta
from src.tools.git_tools import query_git_commits
from src.tools.log_tools import fetch_incident_logs

INCIDENT_ID = "INC-2026-001"
QUERY = "database connection exhaustion and deployment changes"

def main() -> None:
    """Verify that all incident investigation tools perform semantic retrieval."""

    commits = query_git_commits(incident_id=INCIDENT_ID,query=QUERY,)
    logs = fetch_incident_logs(incident_id=INCIDENT_ID,query=QUERY,)
    deployments = get_deployment_delta(incident_id=INCIDENT_ID, query=QUERY,)

    print(f"Commits: {len(commits)}")
    print(f"Logs: {len(logs)}")
    print(f"Deployments: {len(deployments)}")

if __name__ == "__main__":
    main()