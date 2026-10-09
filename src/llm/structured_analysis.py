from src.config import get_config
from src.llm.client import create_openai_client
from src.schemas.incident import IncidentReport

def investigate_incident() -> IncidentReport:
    """Generate a structured incident report from a simple test incident."""

    client = create_openai_client()
    config = get_config()
    response = client.responses.parse(
        model=config.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a software incident investigator. "
                    "Analyze the incident and return a structured "
                    "root-cause analysis."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Our production API started returning HTTP 500 errors "
                    "shortly after a deployment. The errors mention that "
                    "the database connection pool is exhausted."
                ),
            },
        ],
        text_format=IncidentReport,
    )
    return response.output_parsed
