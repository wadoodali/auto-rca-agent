# AI Incident Investigator

AI Incident Investigator is an autonomous incident root-cause analysis agent. It uses an OpenAI model with tool calling, retrieves incident evidence from a ChromaDB-backed RAG store, and returns structured Pydantic reports. The repository also contains deterministic evaluation and an optional semantic evaluation using DeepEval and an independent Groq judge.

## Architecture

- `src/agent/` contains the autonomous investigation loop.
- `src/tools/` contains tool definitions, adapters, execution, and incident-evidence tools.
- `src/rag/` contains document ingestion, ChromaDB storage, and retrieval.
- `src/llm/` contains OpenAI client and structured-analysis integration.
- `src/schemas/` contains structured incident-report models.
- `tests/unit/` contains offline unit tests.
- `tests/evaluation/deterministic/` contains deterministic report checks.
- `tests/evaluation/semantic/` contains optional provider-backed semantic checks.

Run project commands from the repository root. Relative paths for `samples/` and the default ChromaDB location currently depend on that working directory.

## Requirements

- Python 3.14 (the version used by the repository's GitHub Actions workflows).
- A PowerShell terminal on Windows for the setup commands below.
- The pinned dependencies in `requirements.txt`.

## Local setup

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```powershell
python -m pip install -r requirements.txt
```

If PowerShell execution-policy settings prevent activation, use an approved local policy or invoke the environment's Python directly.

## Environment variables

Create a `.env` file in the repository root. Do not commit it; `.env` is ignored by Git. Never place real credentials in source code or documentation.

```dotenv
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PATH=data/chroma
GROQ_API_KEY=your-groq-api-key
```

`OPENAI_API_KEY` is required when OpenAI functionality is used. `GROQ_API_KEY` is required for semantic evaluation. The other values have the defaults shown above and can be overridden for a runtime environment.

## Seed ChromaDB

Seed the sample incidents and initialize the configured persistent ChromaDB collection from the repository root:

```powershell
python scripts/seed_samples.py
```

The default persistent path is `data/chroma` and the collection name is `incident_evidence`. Seeding uses the configured OpenAI embedding model and therefore requires `OPENAI_API_KEY` and provider access.

If `OPENAI_EMBEDDING_MODEL` changes, the existing vector store must be compatible with that model. For a model change, clear the configured Chroma path and reseed it before retrieving evidence. The local Chroma data directory is ignored by Git and is not supplied by a fresh checkout.

## Run one investigation

Configure `OPENAI_API_KEY`, seed ChromaDB, and set `CHROMA_PATH` to the intended store before running an investigation from the repository root:

```python
from src.agent.rca_agent import run_investigation

result = run_investigation(
    incident_id="INC-2026-001",
    investigation_query=(
        "Analyze the incident and identify the likely root cause "
        "using the available logs, commits, and deployment evidence."
    ),
)

print("Likely cause:", result.report.likely_cause)
print("Confidence:", result.report.confidence)
print("Suggested remediation:", result.report.suggested_remediation)
print("Retrieved evidence:", len(result.retrieved_context))
print("Tool calls:", len(result.execution_trace))
```

The investigation uses OpenAI and may incur API costs. The example prints structured report fields and summary counts without dumping the full execution trace or retrieved evidence.

## Tests and evaluations

Run the offline unit suite:

```powershell
python scripts/run_evaluation.py unit
```

Run the deterministic evaluation:

```powershell
python scripts/run_evaluation.py deterministic
```

These suites do not require the semantic Groq judge. The deterministic suite checks configured ground-truth properties such as confidence and introducing commits.

Semantic evaluation is intentionally separate and is only run manually:

```powershell
python -m pytest tests/evaluation/semantic -q
```

Before running it, seed ChromaDB and provide both `OPENAI_API_KEY` and `GROQ_API_KEY`. Semantic evaluation calls external OpenAI and Groq-backed services and may incur API usage costs. It is not part of normal CI; GitHub Actions exposes it through the manually triggered semantic-evaluation workflow.
