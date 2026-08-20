export default function ReportPreview() {
  return (
    <section className="section-gap" id="report">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: 64 }}>
          <p className="overline">Audit Reports</p>
          <h2 className="h2">
            Auditable, <span className="accent">transparent</span> output
          </h2>
          <p style={{ color: "#8a8a8a", maxWidth: 600, margin: "12px auto 0" }}>
            Every investigation produces a structured JSON record and a
            human-readable HTML report — both with full source attribution,
            limitations, and pipeline versioning.
          </p>
        </div>

        <div className="report-preview-layout">
          {/* HTML mockup */}
          <div className="report-html-mockup">
            <div
              style={{
                background: "#BFFF00",
                color: "#111",
                padding: "12px 16px",
                borderRadius: 12,
                fontWeight: 800,
                fontSize: 18,
                marginBottom: 20,
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <span>D</span> DECEPTRIX Audit Report
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>
                Audit Type: Rumour Audit
              </div>
              <div style={{ fontSize: 12, color: "#888" }}>
                ID: RA-2026-08-20-X7K9 · Pipeline: 0.1.0-mvp · Policy:
                gov_in_v1
              </div>
            </div>
            <div
              style={{
                background: "#fff0f0",
                border: "1px solid #ffcccc",
                borderRadius: 8,
                padding: 12,
                marginBottom: 16,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 13, color: "#d32f2f" }}>
                ❌ Outcome: Contradicted
              </div>
              <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                Core claims contradicted by RBI and PIB Fact Check
              </div>
            </div>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 8 }}>
              Source Evidence
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#666",
                lineHeight: 1.8,
                marginBottom: 12,
              }}
            >
              <strong style={{ color: "#111" }}>T1 — Reserve Bank of India:</strong>{" "}
              KYC norms allow multiple forms of officially valid documents...
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#666",
                lineHeight: 1.8,
                marginBottom: 16,
              }}
            >
              <strong style={{ color: "#111" }}>T2 — PIB Fact Check:</strong>{" "}
              The claim that Aadhaar is mandatory for all bank transactions is
              misleading...
            </div>
            <div
              style={{
                background: "#fffde7",
                border: "1px solid #fff9c4",
                borderRadius: 8,
                padding: 12,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 12, color: "#f57f17" }}>
                ⚠️ What this does NOT prove
              </div>
              <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>
                This audit does not guarantee that no Aadhaar-related policy
                change will ever be introduced...
              </div>
            </div>
          </div>

          {/* JSON mockup */}
          <div className="report-json-mockup">
            <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
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
          "event_id": "ev-001",
          "source": "RBI",
          "tier": 1,
          "status": "completed",
          "passage": "KYC norms allow...",
          "url": "rbi.org.in/...",
          "verdict": "contradicts"
        }
      ]
    }
  ],
  "limitations": [
    "Bounded search as of Aug 2026",
    "Not a legal determination"
  ],
  "report_hash": "sha256:a1b2c3..."
}`}
            </pre>
          </div>
        </div>

        <div className="report-actions" style={{ justifyContent: "center", marginTop: 32 }}>
          <button className="btn-primary">
            Download HTML Report <span className="btn-arrow">↓</span>
          </button>
          <button className="btn-secondary">Download JSON</button>
        </div>
      </div>
    </section>
  );
}
