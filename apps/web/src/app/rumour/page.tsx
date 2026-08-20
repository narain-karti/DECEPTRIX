"use client";

import RumourAudit from "../../components/rumour/RumourAudit";

export default function RumourAuditPage() {
  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "32px" }}>
        <span className="section-label">Investigation Tool</span>
        <h1 className="h1" style={{ marginTop: "4px" }}>
          <span className="text-orange">Rumour</span> Audit
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "8px" }}>
          Paste a text claim to extract atomic assertions, retrieve evidence from 4 tiers of sources, and fuse the results.
        </p>
      </div>

      <div 
        style={{ 
          background: "var(--surface-dark)", 
          border: "1px solid var(--border)", 
          borderRadius: "var(--radius-xl)", 
          padding: "32px", 
          boxShadow: "var(--shadow-card)" 
        }}
      >
        <RumourAudit />
      </div>
    </div>
  );
}
