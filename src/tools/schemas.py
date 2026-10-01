GIT_COMMITS_TOOL = {
    "type": "function",
    "name": "query_git_commits",
    "description": (
        "Perform a semantic RAG search against ChromaDB for Git commit "
        "evidence related to a specific incident. Use this tool to find "
        "commits that are relevant to the investigation query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The unique identifier of the incident."
            },
            "query": {
                "type": "string",
                "description": (
                    "A semantic search query describing the commit evidence "
                    "needed for the investigation."
                )
            },
        },
        "required": ["incident_id", "query"],
        "additionalProperties": False,
    },
    "strict": True,
}


INCIDENT_LOGS_TOOL = {
    "type": "function",
    "name": "fetch_incident_logs",
    "description": (
        "Perform a semantic RAG search against ChromaDB for log evidence "
        "related to a specific incident. Use this tool to find log events "
        "that are relevant to the investigation query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The unique identifier of the incident."
            },
            "query": {
                "type": "string",
                "description": (
                    "A semantic search query describing the log evidence "
                    "needed for the investigation."
                )
            },
        },
        "required": ["incident_id", "query"],
        "additionalProperties": False,
    },
    "strict": True,
}


DEPLOYMENT_TOOL = {
    "type": "function",
    "name": "get_deployment_delta",
    "description": (
        "Perform a semantic RAG search against ChromaDB for deployment "
        "evidence related to a specific incident. Use this tool to find "
        "deployments relevant to the investigation query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "incident_id": {
                "type": "string",
                "description": "The unique identifier of the incident."
            },
            "query": {
                "type": "string",
                "description": (
                    "A semantic search query describing the deployment "
                    "evidence needed for the investigation."
                )
            },
        },
        "required": ["incident_id", "query"],
        "additionalProperties": False,
    },
    "strict": True,
}