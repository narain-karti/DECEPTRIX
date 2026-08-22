"use client";
import { useState, useEffect } from "react";

type FlowState = "input" | "processing" | "results" | "failed";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const DEMO_TEXTS = {
  aadhaar: `BREAKING: Government has announced that Aadhaar card will be mandatory for all bank transactions starting January 2027. RBI has issued circular. All accounts without Aadhaar will be frozen. Also, new digital rupee will replace cash completely by March 2027. Share with everyone before it's too late!`,
  pib_factcheck: `PIB India has issued a fake circular claiming that all VPN services must be registered with the Ministry of Electronics by next month. Action will be taken against unregistered users. Forward this to all your contacts.`,
  digital_rupee: `RBI has cancelled all paper currency notes starting next month. Digital Rupee (e-Rupee) will be the only legal tender in India. Old notes can be exchanged at banks until December 2024.`,
  election_rumor: `New EC directive: All opinion polls are banned until after the Lok Sabha results are declared. Any pollster publishing data before that will face criminal charges.`,
};

interface Citation {
  url: string;
  title: string;
  snippet: string;
  tier: number;
}

interface ClaimItem {
  claim_id: string;
  text: string;
  outcome: "Supported" | "Contradicted" | "Unsupported";
  citations: Citation[];
}

interface TextAuditResult {
  id: string;
  status: string;
  progress: number;
  current_step?: string;
  extracted_claims: ClaimItem[];
  audit_trail: any[];
  report_links?: {
    json?: string;
    pdf?: string;
  };
}

export default function RumourAudit() {
  const [flow, setFlow] = useState<FlowState>("input");
  const [text, setText] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Initializing text audit...");
  const [resultData, setResultData] = useState<TextAuditResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  const startAudit = async () => {
    if (text.trim().length < 10) return;
    setFlow("processing");
    setProgress(5);
    setCurrentStep("Submitting text to audit pipeline...");
    setResultData(null);
    setErrorMsg("");

    try {
      const res = await fetch(`${API_BASE}/api/v1/text/audits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setJobId(data.id);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(`Failed to submit text for audit: ${err.message}`);
      setFlow("failed");
    }
  };

  useEffect(() => {
    if (flow !== "processing" || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/text/audits/${jobId}`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data: TextAuditResult = await res.json();

        setProgress(data.progress || 0);
        if (data.current_step) {
          setCurrentStep(data.current_step);
        }

        if (data.status === "completed") {
          clearInterval(interval);
          setResultData(data);
          setFlow("results");
        } else if (data.status === "failed" || data.status === "error") {
          clearInterval(interval);
          setErrorMsg(data.current_step || "The text audit pipeline encountered an error.");
          setFlow("failed");
        }
      } catch (err: any) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [flow, jobId]);

  const reset = () => {
    setFlow("input");
    setText("");
    setJobId(null);
    setProgress(0);
    setResultData(null);
    setErrorMsg("");
  };

  const getTierLabel = (tier: number) => {
    switch (tier) {
      case 1:
        return "T1 · Primary Authority (e.g. .gov.in, PIB, official)";
      case 2:
        return "T2 · Official Fact-Check (e.g. FactCheck, BOOM, AltNews)";
      default:
        return "T3 · Discovery (e.g. blogs, social media)";
    }
  };

  const getOverallVerdict = () => {
    if (!resultData?.extracted_claims?.length) return "Unsupported";
    const outcomes = resultData.extracted_claims.map((c) => c.outcome);
    if (outcomes.includes("Contradicted")) return "Contradicted";
    if (outcomes.includes("Supported")) return "Supported";
    return "Unsupported";
  };

  /* ------ INPUT STATE ------ */
  if (flow === "input") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Paste Claim</span>
        </div>

        <div className="text-input-area">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste a social-media message, forwarded claim, or news rumour here..."
            maxLength={2000}
          />
          <div className="text-input-footer">
            <span className="char-count">{text.length} / 2000</span>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button
                className="btn-ghost"
                style={{ fontSize: "12px", color: "var(--accent)" }}
                onClick={() => setText(DEMO_TEXTS.aadhaar)}
              >
                Preset 1: Aadhaar-Mandate →
              </button>
              <button
                className="btn-ghost"
                style={{ fontSize: "12px" }}
                onClick={() => setText(DEMO_TEXTS.pib_factcheck)}
              >
                Preset 2: PIB Fake Circular →
              </button>
              <button
                className="btn-ghost"
                style={{ fontSize: "12px" }}
                onClick={() => setText(DEMO_TEXTS.digital_rupee)}
              >
                Preset 3: Digital Rupee →
              </button>
              <button
                className="btn-ghost"
                style={{ fontSize: "12px" }}
                onClick={() => setText(DEMO_TEXTS.election_rumor)}
              >
                Preset 4: Election Rumour →
              </button>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 20, display: "flex", gap: "12px", alignItems: "center" }}>
          <button
            className="btn-primary"
            onClick={startAudit}
            disabled={text.trim().length < 10}
            style={{ opacity: text.trim().length < 10 ? 0.4 : 1 }}
          >
            Extract & Audit Claims <span className="btn-arrow">→</span>
          </button>
          {text && (
            <button className="btn-secondary" onClick={() => setText("")}>
              Clear
            </button>
          )}
        </div>

        <div style={{ marginTop: 24 }}>
          <p className="caption">
            🔒 DECEPTRIX connects to DuckDuckGo live discovery and facebook/bart-large-mnli zero-shot classification to cross-examine claims across 3 source authority tiers, with India-specific domain weighting.
          </p>
        </div>
      </div>
    );
  }

  /* ------ PROCESSING STATE ------ */
  if (flow === "processing") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Analyzing & Researching...</span>
        </div>

        <div className="text-input-area" style={{ opacity: 0.5 }}>
          <div style={{ fontSize: 14, color: "var(--text-secondary)", whiteSpace: "pre-wrap" }}>
            {text}
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 40 }}>
          <div style={{ fontSize: 42, marginBottom: 16, animation: "pulse 1.5s infinite" }}>
            🔍
          </div>
          <div className="h4">{currentStep}</div>
          <p className="caption" style={{ marginTop: 8 }}>
            Running real-time source retrieval and NLI entailment classification
          </p>
        </div>

        <div style={{ marginTop: 32, maxWidth: 600, marginInline: "auto" }}>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%`, transition: "width 0.3s ease" }}
            />
          </div>
          <div className="progress-status" style={{ marginTop: 8, display: "flex", justifyContent: "space-between" }}>
            <span className="progress-status-text" style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              {currentStep}
            </span>
            <span className="progress-status-percent" style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>
              {progress}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  /* ------ FAILED STATE ------ */
  if (flow === "failed") {
    return (
      <div style={{ textAlign: "center", padding: "48px 0" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
        <div className="h4" style={{ color: "#ff4d4d", marginBottom: 12 }}>
          Audit Failed
        </div>
        <p className="caption" style={{ maxWidth: 500, margin: "0 auto 24px" }}>
          {errorMsg || "An error occurred during text claim extraction and retrieval."}
        </p>
        <button className="btn-primary" onClick={reset}>
          Try Again
        </button>
      </div>
    );
  }

  /* ------ RESULTS STATE ------ */
  const overallVerdict = getOverallVerdict();
  const claims = resultData?.extracted_claims || [];
  const allCitations: Citation[] = [];
  claims.forEach((c) => {
    (c.citations || []).forEach((cit) => {
      if (!allCitations.some((existing) => existing.url === cit.url)) {
        allCitations.push(cit);
      }
    });
  });

  return (
    <div>
      <div className="flow-step-nav">
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot active" />
        <span className="flow-step-label">Audit Results</span>
      </div>

      {/* Outcome Banner */}
      {overallVerdict === "Contradicted" && (
        <div className="outcome-card outcome-contradicted">
          <div className="outcome-label">
            <span>❌</span> Contradicted by Authoritative Sources
          </div>
          <div className="outcome-desc">
            One or more assertions in this text are contradicted by retrieved authoritative evidence.
            Cross-referencing against verified sources shows factual inconsistencies.
          </div>
        </div>
      )}

      {overallVerdict === "Supported" && (
        <div className="outcome-card" style={{ background: "rgba(46, 213, 115, 0.1)", border: "1px solid rgba(46, 213, 115, 0.3)", borderRadius: "var(--radius-md)", padding: 24 }}>
          <div className="outcome-label" style={{ color: "#2ed573", fontWeight: 700, fontSize: 18, marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
            <span>✅</span> Supported by Available Evidence
          </div>
          <div className="outcome-desc" style={{ color: "var(--text-secondary)", fontSize: 14 }}>
            Claims in this message align with available public domain reporting and official sources.
          </div>
        </div>
      )}

      {overallVerdict === "Unsupported" && (
        <div className="outcome-card" style={{ background: "rgba(255, 171, 0, 0.1)", border: "1px solid rgba(255, 171, 0, 0.3)", borderRadius: "var(--radius-md)", padding: 24 }}>
          <div className="outcome-label" style={{ color: "#ffab00", fontWeight: 700, fontSize: 18, marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
            <span>⚠️</span> Inconclusive / Unsupported
          </div>
          <div className="outcome-desc" style={{ color: "var(--text-secondary)", fontSize: 14 }}>
            Insufficient authoritative evidence found to definitively confirm or refute the extracted claims at this time.
          </div>
        </div>
      )}

      {/* Claim-Level Outcomes */}
      <div className="claims-section" style={{ marginTop: 32 }}>
        <h3 className="h4" style={{ marginBottom: 16 }}>
          Atomic Claim Analysis ({claims.length} claim{claims.length !== 1 ? "s" : ""})
        </h3>
        {claims.map((claim, idx) => (
          <div className="claim-card selected" key={claim.claim_id || idx} style={{ marginBottom: 12 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
                <span className="claim-number">Claim #{idx + 1}</span>
                <span
                  className="tier-badge"
                  style={{
                    background:
                      claim.outcome === "Contradicted"
                        ? "rgba(255,77,77,0.15)"
                        : claim.outcome === "Supported"
                        ? "rgba(46,213,115,0.15)"
                        : "rgba(255,171,0,0.15)",
                    color:
                      claim.outcome === "Contradicted"
                        ? "#ff4d4d"
                        : claim.outcome === "Supported"
                        ? "#2ed573"
                        : "#ffab00",
                  }}
                >
                  {claim.outcome}
                </span>
                <span className="pill-outline" style={{ fontSize: 11 }}>
                  {claim.citations?.length || 0} Source{claim.citations?.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="claim-text" style={{ fontSize: 15, lineHeight: 1.5 }}>
                {claim.text}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Retrieved Sources */}
      <div className="source-cards" style={{ marginTop: 32 }}>
        <h3 className="h4" style={{ marginBottom: 16 }}>
          📚 Retrieved Source Evidence ({allCitations.length})
        </h3>
        {allCitations.length === 0 ? (
          <p className="caption">No external sources retrieved during this audit window.</p>
        ) : (
          allCitations.map((src, i) => (
            <div className={`source-card tier-${src.tier}-border`} key={i} style={{ marginBottom: 16 }}>
              <div className="source-card-header">
                <div className="source-name" style={{ fontWeight: 600 }}>
                  <span>{src.tier === 1 ? "🏛️" : src.tier === 2 ? "✅" : "📰"}</span>
                  {src.title || src.url}
                </div>
                <span className={`tier-badge tier-${src.tier}`}>
                  {getTierLabel(src.tier)}
                </span>
              </div>
              <div className="source-passage" style={{ margin: "10px 0", fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                "{src.snippet}"
              </div>
              <div className="source-meta" style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text-muted)", flexWrap: "wrap" }}>
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "var(--accent)", textDecoration: "underline" }}
                >
                  🔗 {src.url.length > 50 ? src.url.slice(0, 50) + "..." : src.url}
                </a>
              </div>
            </div>
          ))
        )}
      </div>

      {/* What this does NOT prove */}
      <div className="not-prove" style={{ marginTop: 32 }}>
        <div className="not-prove-title">⚠️ What this audit does NOT prove</div>
        <ul>
          <li>
            Source coverage is bounded by the connectors queried at audit time.
          </li>
          <li>
            Results apply to the specific extracted claims, not to the entire unstructured message context.
          </li>
          <li>
            Search results from Tier 3 discovery sources are informative leads, not sole evidentiary proof.
          </li>
          <li>
            This audit is an automated forensic check and does not constitute a legal verdict.
          </li>
        </ul>
      </div>

      {/* Audit metadata */}
      <div className="result-card" style={{ marginTop: 24 }}>
        <div className="result-card-header">
          <div className="result-card-title">🕐 Audit Metadata</div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px" }}>
          {[
            ["Audit ID", resultData?.id || "N/A"],
            ["Modality", "Text & Rumour Cross-Verification"],
            ["Claims Analyzed", `${claims.length}`],
            ["Sources Retrieved", `${allCitations.length}`],
            ["Pipeline Version", "DECEPTRIX v2.0-NLI"],
            ["NLI Entailment Model", "BART-Large-MNLI (Zero-Shot)"],
            ["Search Engine", "DuckDuckGo Live Search API"],
            ["Status", resultData?.status || "completed"],
          ].map(([k, v]) => (
            <div key={k} style={{ padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
              <div className="caption" style={{ marginBottom: 2 }}>{k}</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: 32, display: "flex", gap: 12, flexWrap: "wrap" }}>
        {jobId && (
          <>
            <a
              href={`${API_BASE}/api/v1/reports/${jobId}.pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              Download PDF Report <span className="btn-arrow">↓</span>
            </a>
            <a
              href={`${API_BASE}/api/v1/reports/${jobId}.json`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary"
            >
              Download JSON Record
            </a>
          </>
        )}
        <button className="btn-secondary" onClick={reset}>
          New Audit
        </button>
      </div>
    </div>
  );
}
