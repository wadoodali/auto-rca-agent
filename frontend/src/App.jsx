import { useCallback, useEffect, useState } from "react";
import { fetchIncidents, submitInvestigation } from "./api.js";

const INCIDENT_DETAILS = {
  "INC-2026-001": "The checkout API began returning HTTP 500 responses shortly after a production deployment.",
  "INC-2026-002": "The order API experienced a significant latency increase after a production deployment, causing elevated request timeouts.",
  "INC-2026-003": "Authentication failures began immediately after midnight.",
  "INC-2026-004": "The image-service experienced gradual memory growth over several days and eventually crashed with an out-of-memory error.",
  "INC-2026-005": "The checkout API experienced a sharp increase in payment transaction failures. The incident was caused by an external Stripe API outage returning HTTP 503 responses.",
  "INC-2026-006": "The cart API began accepting invalid cart states after a recent deployment. A later merge-conflict resolution accidentally removed the validation logic and reintroduced the original bug.",
};

function displayPayload(value) {
  if (typeof value === "string") {
    return value;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "Unavailable";
  }
}

function parseContextRecord(value) {
  if (typeof value !== "string") {
    return null;
  }

  try {
    const parsed = JSON.parse(value);
    return parsed !== null && typeof parsed === "object" && !Array.isArray(parsed)
      ? parsed
      : null;
  } catch {
    return null;
  }
}

function ContextRecord({ value, index }) {
  const parsed = parseContextRecord(value);
  const hasContent = parsed && typeof parsed.content === "string";
  const metadata = parsed
    ? [
        ["Source type", parsed.source_type],
        ["Source ID", parsed.source_id],
        ["Incident", parsed.incident_id],
        ["Distance", parsed.distance],
      ].filter(([, item]) => item !== undefined && item !== null)
    : [];

  return (
    <li className="context-record">
      {hasContent ? (
        <>
          <div className="context-metadata">
            {metadata.map(([label, item]) => (
              <span key={label}>
                <strong>{label}</strong> {String(item)}
              </span>
            ))}
          </div>
          <p className="context-content">{parsed.content}</p>
        </>
      ) : (
        <p className="context-content">{displayPayload(value)}</p>
      )}
      <details className="raw-record">
        <summary>View raw record {index + 1}</summary>
        <pre>{displayPayload(value)}</pre>
      </details>
    </li>
  );
}

function ReportSection({ result }) {
  const [activeTab, setActiveTab] = useState("report");
  const report = result?.report;
  const evidence = Array.isArray(report?.evidence)
    ? report.evidence.filter((item) => typeof item === "string")
    : [];
  const retrievedContext = Array.isArray(result?.retrieved_context)
    ? result.retrieved_context
    : [];
  const executionTrace = Array.isArray(result?.execution_trace)
    ? result.execution_trace.filter(
        (entry) => entry !== null && typeof entry === "object",
      )
    : [];

  return (
    <section className="result-region" aria-labelledby="result-title">
      <div className="result-heading">
        <div>
          <p className="eyebrow">Investigation result</p>
          <h2 id="result-title">Root-cause analysis</h2>
        </div>
        <span className="result-confidence">
          Reported confidence: {typeof report?.confidence === "number" ? report.confidence : "Unavailable"}
        </span>
      </div>

      <div className="result-tabs" role="tablist" aria-label="Investigation result views">
        {[
          ["report", "RCA Report"],
          ["context", `Retrieved Context (${retrievedContext.length})`],
          ["trace", `Execution Trace (${executionTrace.length})`],
        ].map(([tab, label]) => (
          <button
            key={tab}
            className={`result-tab ${activeTab === tab ? "active" : ""}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`panel-${tab}`}
            id={`tab-${tab}`}
            onClick={() => setActiveTab(tab)}
          >
            {label}
          </button>
        ))}
      </div>

      {activeTab === "report" && (
        <div id="panel-report" role="tabpanel" aria-labelledby="tab-report" className="tab-panel">
          <div className="conclusion-block">
            <p className="field-label">Likely cause</p>
            <p className="conclusion-text">
              {typeof report?.likely_cause === "string"
                ? report.likely_cause
                : "No likely cause was returned."}
            </p>
          </div>
          <div className="report-columns">
            <div className="report-block">
              <p className="field-label">Evidence</p>
              {evidence.length > 0 ? (
                <ul className="evidence-list">
                  {evidence.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
                </ul>
              ) : <p className="empty-result">No supporting evidence was returned.</p>}
            </div>
            <div className="report-block remediation-block">
              <p className="field-label">Suggested remediation</p>
              <p>{typeof report?.suggested_remediation === "string" ? report.suggested_remediation : "No remediation was returned."}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === "context" && (
        <div id="panel-context" role="tabpanel" aria-labelledby="tab-context" className="tab-panel">
          {retrievedContext.length > 0 ? (
            <ul className="context-list">
              {retrievedContext.map((item, index) => <ContextRecord key={`context-${index}`} value={item} index={index} />)}
            </ul>
          ) : <p className="empty-result">No retrieved context was returned.</p>}
        </div>
      )}

      {activeTab === "trace" && (
        <div id="panel-trace" role="tabpanel" aria-labelledby="tab-trace" className="tab-panel">
          {executionTrace.length > 0 ? (
            <div className="trace-list">
              {executionTrace.map((entry, index) => (
                <article className="trace-entry" key={`${entry.tool_name ?? "trace"}-${index}`}>
                  <div className="trace-header">
                    <strong>{typeof entry.tool_name === "string" ? entry.tool_name : "Unnamed tool call"}</strong>
                    <span>Round {typeof entry.round === "number" ? entry.round : "?"}</span>
                    <span className={`trace-status trace-status-${entry.status ?? "unknown"}`}>
                      {typeof entry.status === "string" ? entry.status : "status unavailable"}
                    </span>
                    <span>Results {typeof entry.result_count === "number" ? entry.result_count : "?"}</span>
                  </div>
                  {entry.tool_call !== undefined && <div className="trace-payload"><p className="payload-label">Tool arguments / request</p><pre>{displayPayload(entry.tool_call)}</pre></div>}
                  {entry.result !== undefined && <div className="trace-payload"><p className="payload-label">Tool result</p><pre>{displayPayload(entry.result)}</pre></div>}
                </article>
              ))}
            </div>
          ) : <p className="empty-result">No tool calls were recorded.</p>}
        </div>
      )}
    </section>
  );
}

function AboutPage({ onNavigate }) {
  return (
    <section className="about-page" aria-labelledby="about-title">
      <p className="eyebrow">About the project</p>
      <h1 id="about-title">Building practical AI systems.</h1>
      <div className="about-copy">
        <section className="about-section" aria-labelledby="about-me-title">
          <h2 id="about-me-title">About me</h2>
          <p>
            I am a Computer Science &amp; Artificial Intelligence bachelor&apos;s
            student at Technische Hochschule Ingolstadt, interested in AI
            engineering and practical AI systems.
          </p>
        </section>
        <section className="about-section" aria-labelledby="about-project-title">
          <h2 id="about-project-title">About the project</h2>
          <p>
            AI Incident Investigator is a portfolio project that analyzes
            software incidents using logs, Git commit information, deployment
            history, retrieval, and tool-using agent workflows. It produces
            structured reports with a likely cause, supporting evidence,
            confidence, and suggested remediation.
          </p>
        </section>
        <section className="about-section" aria-labelledby="technical-highlights-title">
          <h2 id="technical-highlights-title">Technical highlights</h2>
          <p>
            Python, Pydantic, FastAPI, React, Vite, ChromaDB,
            retrieval-augmented generation, tool execution and incident
            isolation, automated testing, deterministic and semantic
            evaluation, and CI.
          </p>
        </section>
        <section className="about-section" aria-labelledby="project-link-title">
          <h2 id="project-link-title">Project link</h2>
          <p>
            <a
              className="about-link"
              href="https://github.com/wadoodali/auto-rca-agent"
              target="_blank"
              rel="noreferrer"
            >
              View the project on GitHub
            </a>
          </p>
        </section>
        <button className="about-return" type="button" onClick={() => onNavigate("/")}>
          Return to investigation
        </button>
      </div>
    </section>
  );
}

function App() {
  const [route, setRoute] = useState(
    () => (window.location.pathname === "/about" ? "about" : "investigate"),
  );
  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState("");
  const [incidentState, setIncidentState] = useState("loading");
  const [incidentError, setIncidentError] = useState("");
  const [investigationQuery, setInvestigationQuery] = useState("");
  const [queryError, setQueryError] = useState("");
  const [submissionState, setSubmissionState] = useState("idle");
  const [submissionError, setSubmissionError] = useState("");
  const [investigationResult, setInvestigationResult] = useState(null);

  const navigate = useCallback((path) => {
    window.history.pushState({}, "", path);
    setRoute(path === "/about" ? "about" : "investigate");
  }, []);

  const loadIncidents = useCallback(async () => {
    setIncidentState("loading");
    setIncidentError("");

    try {
      const loadedIncidents = await fetchIncidents();
      setIncidents(loadedIncidents);
      setSelectedIncidentId((currentId) => {
        if (loadedIncidents.some(({ incident_id }) => incident_id === currentId)) {
          return currentId;
        }
        return loadedIncidents[0]?.incident_id ?? "";
      });
      setIncidentState(loadedIncidents.length > 0 ? "connected" : "empty");
    } catch (error) {
      setIncidents([]);
      setSelectedIncidentId("");
      setIncidentError(
        error instanceof Error
          ? error.message
          : "The investigation API could not load incidents.",
      );
      setIncidentState("error");
    }
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(window.location.pathname === "/about" ? "about" : "investigate");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (route === "investigate") {
      void loadIncidents();
    }
  }, [loadIncidents, route]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmedQuery = investigationQuery.trim();

    if (!trimmedQuery) {
      setQueryError("Enter a question before starting the investigation.");
      return;
    }

    if (!selectedIncidentId || submissionState === "submitting") {
      return;
    }

    setQueryError("");
    setSubmissionError("");
    setSubmissionState("submitting");
    setInvestigationResult(null);

    try {
      const result = await submitInvestigation(
        selectedIncidentId,
        trimmedQuery,
      );
      setInvestigationResult(result);
      setSubmissionState("success");
    } catch (error) {
      setSubmissionError(
        error instanceof Error
          ? error.message
          : "The investigation could not be completed.",
      );
      setSubmissionState("error");
    }
  };

  const canSubmit =
    incidentState === "connected" &&
    Boolean(selectedIncidentId) &&
    investigationQuery.trim().length > 0 &&
    submissionState !== "submitting";

  const statusLabel = {
    loading: "Loading incidents",
    connected: "API connected",
    empty: "No incidents",
    error: "API unavailable",
  }[incidentState];

  return (
    <main className="workspace-shell">
      <header className="topbar">
        <a
          className="brand"
          href="/"
          aria-label="AI Incident Investigator home"
          onClick={(event) => {
            event.preventDefault();
            navigate("/");
          }}
        >
          <img className="brand-illustration" src="/images/neon-robot-header.png" alt="" aria-hidden="true" />
          <span className="brand-copy">
            <span className="brand-wordmark"><span>AI</span> INVESTIGATION</span>
            <span className="brand-tagline">Find the cause behind incidents</span>
          </span>
        </a>
        <nav className="site-nav" aria-label="Primary navigation">
          <a
            className={route === "investigate" ? "active" : ""}
            href="/"
            aria-current={route === "investigate" ? "page" : undefined}
            onClick={(event) => {
              event.preventDefault();
              navigate("/");
            }}
          >
            Investigate
          </a>
          <a
            className={route === "about" ? "active" : ""}
            href="/about"
            aria-current={route === "about" ? "page" : undefined}
            onClick={(event) => {
              event.preventDefault();
              navigate("/about");
            }}
          >
            About
          </a>
          <span className="system-glyph" aria-label="Dark theme">◌</span>
        </nav>
      </header>

      {route === "investigate" && <section className="hero" aria-labelledby="workspace-title">
        <div className="hero-art">
          <img
            className="hero-illustration"
            src="/images/robot-investigator.png"
            alt="Robot investigator reviewing logs, deployments, and code changes"
          />
        </div>
        <div className="hero-copy">
          <p className="eyebrow">Evidence-led RCA</p>
          <h1 id="workspace-title">Incidents happen.<br /><span>Find the cause.</span></h1>
          <p className="intro-copy">
            Use AI to investigate incidents with logs, deployments, and code changes.
            Get a clear root cause, supporting evidence, and recommended fixes.
          </p>
        </div>
      </section>}

      <div className="post-hero">
      {route === "about" ? <AboutPage onNavigate={navigate} /> : <>
      <section id="investigate" className="control-panel" aria-label="Investigation controls">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker"><span className="search-glyph" aria-hidden="true">⌕</span> Investigate an incident</p>
            </div>
            <span className={`status-indicator status-${incidentState}`}>
              {statusLabel}
            </span>
          </div>

          <label className="field-label" htmlFor="incident-select">
            Incident / signal
          </label>
          <form onSubmit={handleSubmit}>
            <select
              id="incident-select"
              className="field-control"
              value={selectedIncidentId}
              onChange={(event) => setSelectedIncidentId(event.target.value)}
              disabled={
                incidentState === "loading" ||
                incidents.length === 0 ||
                submissionState === "submitting"
              }
            >
            {incidentState === "loading" && (
              <option value="">Loading incidents...</option>
            )}
            {incidentState === "empty" && (
              <option value="">No incidents available</option>
            )}
            {incidents.map(({ incident_id }) => (
              <option key={incident_id} value={incident_id}>
                {incident_id} / {INCIDENT_DETAILS[incident_id] ?? "Recorded incident"}
              </option>
            ))}
            </select>

            {incidentState === "error" && (
              <div className="incident-error" role="alert">
                <p>{incidentError}</p>
                <button className="retry-button" type="button" onClick={loadIncidents}>
                  Retry connection
                </button>
              </div>
            )}

            <label className="field-label query-label" htmlFor="investigation-query">
              Investigation question
            </label>
            <textarea
              id="investigation-query"
              className="field-control query-control"
              value={investigationQuery}
              onChange={(event) => {
                setInvestigationQuery(event.target.value);
                if (queryError) {
                  setQueryError("");
                }
              }}
              placeholder="What changed, and what evidence points to the root cause?"
              rows="5"
              disabled={submissionState === "submitting"}
              aria-describedby={queryError ? "query-error" : undefined}
            />
            {queryError && (
              <p id="query-error" className="field-error" role="alert">
                {queryError}
              </p>
            )}

            <button
              className="primary-button"
              type="submit"
              disabled={!canSubmit}
            >
              {submissionState === "submitting"
                ? "Investigating…"
                : "Start investigation"}
            </button>

            {submissionState === "success" && investigationResult && (
              <p className="submission-success" role="status">
                Investigation complete. The structured result is ready for review.
              </p>
            )}

            {submissionState === "error" && (
              <div className="submission-error" role="alert">
                <p>{submissionError}</p>
                <p className="submission-hint">
                  Edit the question or retry when the API is available.
                </p>
              </div>
            )}
          </form>
      </section>

      {investigationResult && <section id="incidents"><ReportSection result={investigationResult} /></section>}
      </>}

      <footer id="about" className="workspace-footer">
        <span>OpenAI model + ChromaDB evidence layer</span>
        <span>Prototype workspace / local analysis</span>
      </footer>
      </div>
    </main>
  );
}

export default App;
