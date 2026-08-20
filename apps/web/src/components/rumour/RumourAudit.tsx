"use client";
import { useState, useEffect } from "react";

type FlowState = "input" | "extracting" | "researching" | "results";

const DEMO_TEXT = `BREAKING: Government has announced that Aadhaar card will be mandatory for all bank transactions starting January 2027. RBI has issued circular. All accounts without Aadhaar will be frozen. Also, new digital rupee will replace cash completely by March 2027. Share with everyone before it's too late!`;

const MOCK_CLAIMS = [
  {
    id: 1,
    text: "Aadhaar card will be mandatory for all bank transactions starting January 2027",
    domain: "Government Policy",
    selected: true,
  },
  {
    id: 2,
    text: "RBI has issued a circular mandating Aadhaar for bank transactions",
    domain: "Financial Regulation",
    selected: true,
  },
  {
    id: 3,
    text: "Bank accounts without Aadhaar will be frozen",
    domain: "Financial Regulation",
    selected: true,
  },
  {
    id: 4,
    text: "Digital rupee will replace cash completely by March 2027",
    domain: "Government Policy",
    selected: false,
  },
];

const MOCK_SOURCES = [
  {
    name: "PIB Fact Check",
    tier: 2,
    tierLabel: "Official Fact-Check",
    passage:
      "The claim that Aadhaar is mandatory for all bank transactions is misleading. RBI has clarified that Aadhaar-based KYC is one of several accepted verification methods. No circular mandating exclusive Aadhaar use has been issued.",
    date: "August 2026",
    url: "pib.gov.in/factcheck",
    verdict: "contradicted",
  },
  {
    name: "Reserve Bank of India",
    tier: 1,
    tierLabel: "Primary Authority",
    passage:
      "KYC norms allow multiple forms of officially valid documents including Aadhaar, PAN, Voter ID, Driving Licence, and Passport. No single document is mandated as the exclusive requirement.",
    date: "July 2026",
    url: "rbi.org.in/scripts/BS_CircularIndexDisplay.aspx",
    verdict: "contradicted",
  },
  {
    name: "Google Fact Check",
    tier: 2,
    tierLabel: "Official Fact-Check",
    passage:
      "Multiple fact-checkers have rated similar claims as False. The digital rupee (e-₹) pilot is ongoing but no timeline for cash replacement has been announced by RBI or the Government.",
    date: "August 2026",
    url: "toolbox.google.com/factcheck",
    verdict: "contradicted",
  },
  {
    name: "Economic Times",
    tier: 3,
    tierLabel: "Discovery",
    passage:
      "RBI Governor stated that the digital rupee pilot continues in select cities. Cash remains legal tender with no plans for discontinuation.",
    date: "August 14, 2026",
    url: "economictimes.com",
    verdict: "context",
  },
];

export default function RumourAudit() {
  const [flow, setFlow] = useState<FlowState>("input");
  const [text, setText] = useState("");
  const [claims, setClaims] = useState(MOCK_CLAIMS);
  const [researchStep, setResearchStep] = useState(0);

  const handleExtract = () => {
    if (text.trim().length < 10) return;
    setFlow("extracting");
    setTimeout(() => setFlow("researching"), 1800);
  };

  useEffect(() => {
    if (flow !== "researching") return;
    if (researchStep >= MOCK_SOURCES.length) {
      setTimeout(() => setFlow("results"), 600);
      return;
    }
    const timer = setTimeout(
      () => setResearchStep((p) => p + 1),
      600 + Math.random() * 400
    );
    return () => clearTimeout(timer);
  }, [flow, researchStep]);

  const toggleClaim = (id: number) => {
    setClaims((prev) =>
      prev.map((c) => (c.id === id ? { ...c, selected: !c.selected } : c))
    );
  };

  const reset = () => {
    setFlow("input");
    setText("");
    setClaims(MOCK_CLAIMS);
    setResearchStep(0);
  };

  const tierClass = (t: number) => `tier-${t}`;

  /* ------ INPUT STATE ------ */
  if (flow === "input") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
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
            <button
              className="btn-ghost"
              onClick={() => setText(DEMO_TEXT)}
            >
              Load demo claim →
            </button>
          </div>
        </div>

        <div style={{ marginTop: 20 }}>
          <button
            className="btn-primary"
            onClick={handleExtract}
            style={{ opacity: text.trim().length < 10 ? 0.4 : 1 }}
          >
            Extract Claims <span className="btn-arrow" style={{ background: "white", color: "var(--dark)" }}>→</span>
          </button>
        </div>

        <div style={{ marginTop: 24 }}>
          <p className="caption">
            ⚠️ Do not paste personal or sensitive information. DECEPTRIX does
            not store text after analysis. Claims are processed in English.
          </p>
        </div>
      </div>
    );
  }

  /* ------ EXTRACTING STATE ------ */
  if (flow === "extracting") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Extracting Claims...</span>
        </div>

        <div className="text-input-area" style={{ opacity: 0.5 }}>
          <div style={{ fontSize: 14, color: "#8a8a8a", whiteSpace: "pre-wrap" }}>
            {text}
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 48 }}>
          <div style={{ fontSize: 40, marginBottom: 16, animation: "pulse 1.5s infinite" }}>
            🧠
          </div>
          <div className="h4">Extracting atomic claims...</div>
          <p className="caption" style={{ marginTop: 8 }}>
            Breaking down the text into specific, checkable assertions
          </p>
        </div>
      </div>
    );
  }

  /* ------ RESEARCHING STATE ------ */
  if (flow === "researching") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Researching Sources...</span>
        </div>

        <div className="claims-section">
          <div className="claims-header">
            <h3 className="h4">
              Extracted Claims ({claims.filter((c) => c.selected).length} selected)
            </h3>
          </div>
          {claims.map((claim) => (
            <div
              className={`claim-card${claim.selected ? " selected" : ""}`}
              key={claim.id}
              onClick={() => toggleClaim(claim.id)}
            >
              <div className="claim-checkbox">
                {claim.selected ? "✓" : ""}
              </div>
              <div>
                <div className="claim-number">Claim #{claim.id}</div>
                <div className="claim-text">{claim.text}</div>
                <div className="claim-domain">
                  <span className="pill-outline" style={{ fontSize: 11 }}>
                    {claim.domain}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 32 }}>
          <div className="h4" style={{ marginBottom: 16 }}>
            🔍 Searching sources...
          </div>
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${(researchStep / MOCK_SOURCES.length) * 100}%` }}
            />
          </div>
          <div className="progress-status" style={{ marginTop: 8 }}>
            <span className="progress-status-text">
              {researchStep < MOCK_SOURCES.length
                ? `Querying: ${MOCK_SOURCES[researchStep].name}...`
                : "Composing audit..."}
            </span>
            <span className="progress-status-percent">
              {Math.round((researchStep / MOCK_SOURCES.length) * 100)}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  /* ------ RESULTS STATE ------ */
  return (
    <div>
      <div className="flow-step-nav">
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot active" />
        <span className="flow-step-label">Audit Results</span>
      </div>

      {/* Outcome */}
      <div className="outcome-card outcome-contradicted">
        <div className="outcome-label">
          <span>❌</span> Contradicted by Authoritative Sources
        </div>
        <div className="outcome-desc">
          The core claims in this message are contradicted by official
          statements from RBI and PIB Fact Check. No RBI circular mandating
          exclusive Aadhaar use exists. No timeline for cash replacement has
          been announced.
        </div>
      </div>

      {/* Claims with outcomes */}
      <div className="claims-section" style={{ marginTop: 32 }}>
        <h3 className="h4" style={{ marginBottom: 16 }}>
          Claim-Level Outcomes
        </h3>
        {claims
          .filter((c) => c.selected)
          .map((claim, i) => (
            <div className="claim-card selected" key={claim.id}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span className="claim-number">Claim #{claim.id}</span>
                  <span
                    className="tier-badge"
                    style={{
                      background: "rgba(255,77,77,0.15)",
                      color: "#ff4d4d",
                    }}
                  >
                    Contradicted
                  </span>
                </div>
                <div className="claim-text">{claim.text}</div>
              </div>
            </div>
          ))}
      </div>

      {/* Source cards */}
      <div className="source-cards" style={{ marginTop: 32 }}>
        <h3 className="h4" style={{ marginBottom: 16 }}>
          📚 Source Evidence
        </h3>
        {MOCK_SOURCES.map((src, i) => (
          <div className={`source-card tier-${src.tier}-border`} key={i}>
            <div className="source-card-header">
              <div className="source-name">
                <span>
                  {src.tier === 1 ? "🏛️" : src.tier === 2 ? "✅" : "📰"}
                </span>
                {src.name}
              </div>
              <span className={`tier-badge ${tierClass(src.tier)}`}>
                T{src.tier} · {src.tierLabel}
              </span>
            </div>
            <div className="source-passage">{src.passage}</div>
            <div className="source-meta">
              <span className="source-meta-item">📅 {src.date}</span>
              <span className="source-meta-item">🔗 {src.url}</span>
              <span className="source-meta-item">
                {src.verdict === "contradicted"
                  ? "❌ Contradicts claim"
                  : "ℹ️ Provides context"}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* What this does NOT prove */}
      <div className="not-prove">
        <div className="not-prove-title">⚠️ What this audit does NOT prove</div>
        <ul>
          <li>
            This audit does not guarantee that no Aadhaar-related policy change
            will ever be introduced
          </li>
          <li>
            Source coverage is bounded by the connectors queried at audit time
            (August 2026)
          </li>
          <li>
            Results apply to the specific extracted claims, not to the entire
            pasted message
          </li>
          <li>
            Search results from Tier 3 sources are leads, not evidence — they
            cannot alone determine the audit outcome
          </li>
          <li>
            This audit is not a legal determination and should not be cited as
            one
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
            ["Audit ID", "RA-2026-08-20-X7K9"],
            ["Timestamp", "2026-08-20T11:00:00Z"],
            ["Claims Analyzed", "3 of 4"],
            ["Sources Queried", "4"],
            ["Pipeline Version", "0.1.0-mvp"],
            ["Policy Pack", "gov_in_v1"],
            ["Language", "English"],
            ["Search Bounded", "Yes"],
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
        <button className="btn-primary">
          Download Report <span className="btn-arrow" style={{ background: "white", color: "var(--dark)" }}>↓</span>
        </button>
        <button className="btn-secondary">Download JSON</button>
        <button className="btn-secondary" onClick={reset}>
          New Audit
        </button>
      </div>
    </div>
  );
}
