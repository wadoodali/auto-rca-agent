import json
from pathlib import Path
from typing import Any
from src.rag.document import EvidenceDocument

def log_to_document(log_entry: dict[str, Any], incident_id: str,) -> EvidenceDocument:
    """Convert a structured log entry into a searchable evidence document."""

    content = log_entry["message"]
    source_id = log_entry.get("request_id", log_entry["timestamp"])
    return EvidenceDocument(content=content, source_type="log", incident_id=incident_id, source_id=source_id,)

def load_log_documents(logs_path: Path, incident_id: str,) -> list[EvidenceDocument]:
    """Load log records from JSON and convert them into evidence documents."""

    with logs_path.open("r", encoding="utf-8") as file:
        log_entries: list[dict[str, Any]] = json.load(file)
    return [
        log_to_document(log_entry, incident_id)
        for log_entry in log_entries
    ]

def commit_to_document(commit: dict[str, Any], incident_id: str,) -> EvidenceDocument:
    """Convert a structured commit record into a searchable evidence document."""

    content = (
        f"Commit message: {commit['message']}. "
        f"Changed files: {', '.join(commit['files_changed'])}. "
        f"Diff: {commit['diff']}"
    )
    return EvidenceDocument(content=content, source_type="commit", incident_id=incident_id, source_id=commit["commit_hash"],)

def load_commit_documents(commits_path: Path, incident_id: str,) -> list[EvidenceDocument]:
    """Load commit records from JSON and convert them into evidence documents."""

    with commits_path.open("r", encoding="utf-8") as file:
        commits: list[dict[str, Any]] = json.load(file)
    return [
        commit_to_document(commit, incident_id)
        for commit in commits
    ]

def deployment_to_document(deployment: dict[str, Any], incident_id: str,) -> EvidenceDocument:
    """Convert a deployment record into a searchable evidence document."""

    content = (
        f"Service: {deployment['service']}. "
        f"Environment: {deployment['environment']}. "
        f"Deployment version: {deployment['version']}. "
        f"Commit: {deployment['commit_hash']}. "
        f"Status: {deployment['status']}."
    )
    return EvidenceDocument(content=content, source_type="deployment", incident_id=incident_id, source_id=deployment["deployment_id"],)

def load_deployment_documents(deployments_path: Path, incident_id: str,) -> list[EvidenceDocument]:
    """Load deployment records from JSON and convert them into evidence documents."""

    with deployments_path.open("r", encoding="utf-8") as file:
        deployments: list[dict[str, Any]] = json.load(file)
    return [
        deployment_to_document(deployment, incident_id)
        for deployment in deployments
    ]

def load_incident_documents(incident_directory: Path, incident_id: str,) -> list[EvidenceDocument]:
    """Load all searchable evidence for an incident."""

    documents: list[EvidenceDocument] = []
    documents.extend(load_log_documents(incident_directory / "logs.json", incident_id,))
    documents.extend(load_commit_documents(incident_directory / "commits.json", incident_id,))
    documents.extend(load_deployment_documents(incident_directory / "deployments.json", incident_id,))

    return documents