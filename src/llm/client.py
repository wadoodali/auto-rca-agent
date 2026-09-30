import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
def create_openai_client() -> OpenAI:
    """Create an OpenAI client using the configured API key."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)