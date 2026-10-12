const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function isIncidentSummary(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    typeof value.incident_id === "string" &&
    value.incident_id.trim().length > 0
  );
}

export async function fetchIncidents() {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/api/incidents`);
  } catch {
    throw new Error("The investigation API could not be reached.");
  }

  if (!response.ok) {
    throw new Error("The investigation API could not load incidents.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("The investigation API returned an invalid response.");
  }

  if (!Array.isArray(payload) || !payload.every(isIncidentSummary)) {
    throw new Error("The investigation API returned an invalid response.");
  }

  return payload;
}

function isInvestigationResult(value) {
  if (value === null || typeof value !== "object") {
    return false;
  }

  const report = value.report;
  return (
    report !== null &&
    typeof report === "object" &&
    typeof report.likely_cause === "string" &&
    Array.isArray(report.evidence) &&
    report.evidence.every((item) => typeof item === "string") &&
    typeof report.confidence === "number" &&
    typeof report.suggested_remediation === "string" &&
    Array.isArray(value.retrieved_context) &&
    value.retrieved_context.every((item) => typeof item === "string") &&
    Array.isArray(value.execution_trace) &&
    value.execution_trace.every(
      (item) => item !== null && typeof item === "object",
    )
  );
}

export async function submitInvestigation(incidentId, investigationQuery) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/api/investigations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        incident_id: incidentId,
        investigation_query: investigationQuery,
      }),
    });
  } catch {
    throw new Error("The investigation request could not be reached.");
  }

  if (!response.ok) {
    throw new Error("The investigation could not be completed.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("The investigation API returned an invalid response.");
  }

  if (!isInvestigationResult(payload)) {
    throw new Error("The investigation API returned an invalid response.");
  }

  return payload;
}
