"use client";

import MediaAudit from "../../components/media/MediaAudit";

export default function MediaAuditPage() {
  return (
    <div style={{ maxWidth: "900px", margin: "0 auto" }}>
      <div style={{ marginBottom: "32px" }}>
        <span className="section-label">Investigation Tool</span>
        <h1 className="h1" style={{ marginTop: "4px" }}>
          <span className="text-orange">Media</span> Audit
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginTop: "8px" }}>
          Upload a video to analyze frames for manipulation, check technical metadata, and verify provenance credentials.
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
        <MediaAudit />
      </div>
    </div>
  );
}
