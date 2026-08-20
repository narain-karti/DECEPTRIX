"use client";

export default function ReportPreview() {
  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Audit Logs</span>
          <h2 className="section-header-title">Auditable, Transparent Output Schema</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "600px" }}>
        Every investigation produces a structured JSON record and a human-readable report with full source attribution.
      </p>

      <div className="report-preview-layout">
        {/* HTML mockup */}
        <div className="report-html-mockup" style={{ padding: "24px" }}>
          <div
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              fontWeight: 800,
              fontSize: 16,
              marginBottom: 20,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span style={{ color: "var(--accent)" }}>D</span> DECEPTRIX Audit Report
          </div>
          
          <div style={{ marginBottom: 16, borderBottom: "1px solid var(--border-light)", paddingBottom: "12px" }}>
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4, color: "var(--text-primary)" }}>
              Audit Type: Rumour Audit
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
              ID: RA-2026-08-20-X7K9 · Pipeline: 0.1.0-mvp · Policy: gov_in_v1
            </div>
          </div>
          
          <div
            style={{
              background: "rgba(255, 77, 77, 0.06)",
              border: "1px solid rgba(255, 77, 77, 0.15)",
              borderRadius: "var(--radius-sm)",
              padding: 12,
              marginBottom: 16,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 13, color: "#ff4d4d" }}>
              ❌ Outcome: Contradicted
            </div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
              Core claims contradicted by RBI and PIB Fact Check
            </div>
          </div>

          <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8, color: "var(--text-primary)" }}>
            Source Evidence
          </div>
          <div
            style={{
              fontSize: 12,
              color: "var(--text-secondary)",
              lineHeight: 1.6,
              marginBottom: 10,
            }}
          >
            <strong style={{ color: "var(--text-primary)" }}>T1 — Reserve Bank of India:</strong>{" "}
            KYC norms allow multiple forms of officially valid documents...
          </div>
          <div
            style={{
              fontSize: 12,
              color: "var(--text-secondary)",
              lineHeight: 1.6,
              marginBottom: 16,
            }}
          >
            <strong style={{ color: "var(--text-primary)" }}>T2 — PIB Fact Check:</strong>{" "}
            The claim that Aadhaar is mandatory for all bank transactions is misleading...
          </div>
          
          <div
            style={{
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              padding: 12,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 12, color: "var(--text-primary)" }}>
              ⚠️ What this does NOT prove
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              This audit does not guarantee that no Aadhaar-related policy change will ever be introduced...
            </div>
          </div>
        </div>

        {/* JSON mockup */}
        <div className="report-json-mockup" style={{ fontSize: "11px", lineHeight: "1.4" }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "#a5d6ff" }}>
            {`{
  "report_version": "1.0.0",
  "audit_id": "RA-2026-08-20-X7K9",
  "audit_type": "rumour",
  "timestamp": "2026-08-20T11:00:00Z",
  "pipeline_version": "0.1.0-mvp",
  "policy_pack": "gov_in_v1",
  "outcome": "contradicted",
  "claims": [
    {
      "claim_id": 1,
      "text": "Aadhaar mandatory for...",
      "outcome": "contradicted",
      "evidence": [
        {
          "source": "RBI",
          "tier": 1,
          "verdict": "contradicts"
        }
      ]
    }
  ]
}`}
          </pre>
        </div>
      </div>

      <div className="report-actions" style={{ justifyContent: "center", marginTop: 24 }}>
        <button className="btn-primary" onClick={() => alert("Downloading HTML report mockup...")}>
          Download HTML Report <span className="btn-arrow">↓</span>
        </button>
        <button className="btn-secondary" onClick={() => alert("Downloading JSON schema...")}>
          Download JSON
        </button>
      </div>
    </div>
  );
}
