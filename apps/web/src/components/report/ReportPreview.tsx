"use client";

import { useState } from "react";
import Link from "next/link";

export default function ReportPreview() {
  const [copied, setCopied] = useState(false);

  const sampleJson = `{
  "report_version": "2.0.0",
  "pipeline_version": "2.0.0-multi-modal",
  "audit_id": "DX-CASE-9921-X7",
  "modality": "media",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "verdict": "Likely Manipulated",
  "composite_anomaly_score": 0.74,
  "signal_breakdown": {
    "vit_deepfake_classifier": 0.82,
    "lip_sync_correlation": 0.65,
    "facial_landmark_jitter": 0.48,
    "dct_spectral_anomaly": 0.71,
    "metadata_container_check": 0.15
  },
  "audit_record_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
}`;

  const copySchema = () => {
    navigator.clipboard.writeText(sampleJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Audit Logs & Export</span>
          <h2 className="section-header-title">Auditable, Tamper-Evident Output Schema</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "680px" }}>
        Every completed investigation outputs a cryptographically hashed JSON record and a formatted PDF forensic audit report.
      </p>

      <div className="report-preview-layout">
        {/* Visual Report Card Mockup */}
        <div className="report-html-mockup" style={{ padding: "24px" }}>
          <div
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              padding: "12px 16px",
              borderRadius: "var(--radius-md)",
              fontWeight: 800,
              fontSize: 15,
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span style={{ color: "var(--accent)" }}>DX</span> DECEPTRIX Forensic Audit Report
          </div>
          
          <div style={{ marginBottom: 14, borderBottom: "1px solid var(--border-light)", paddingBottom: "10px" }}>
            <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>
              Case: DX-CASE-9921-X7 · Modality: Multi-Modal Video
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace", marginTop: "2px" }}>
              SHA-256: e3b0c44298fc1c14... · Pipeline: v2.0-Ensemble
            </div>
          </div>
          
          <div
            style={{
              background: "rgba(255, 77, 77, 0.08)",
              border: "1px solid rgba(255, 77, 77, 0.25)",
              borderRadius: "var(--radius-sm)",
              padding: 12,
              marginBottom: 14,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 13, color: "#ff4d4d" }}>
              🚨 Verdict: Likely Manipulated (Score: 0.74 / 1.00)
            </div>
            <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
              High-confidence generative ViT texture anomalies & lip-sync desynchronization.
            </div>
          </div>

          <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 6, color: "var(--text-primary)" }}>
            Ensemble Signal Findings
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 8 }}>
            <strong style={{ color: "var(--text-primary)" }}>• ViT Patch-16 Classifier:</strong> 82% Generative Facial Texture Risk
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 14 }}>
            <strong style={{ color: "var(--text-primary)" }}>• Lip-Sync Correlation:</strong> Low acoustic-visual temporal alignment (r = 0.12)
          </div>
          
          <div
            style={{
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              padding: 10,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 11, color: "var(--text-primary)" }}>
              🔒 Cryptographic Attestation
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2, fontFamily: "monospace" }}>
              Signature: SHA-256(Audit Payload) = 7f83b1657ff1fc53...
            </div>
          </div>
        </div>

        {/* JSON mockup */}
        <div className="report-json-mockup" style={{ fontSize: "11px", lineHeight: "1.4" }}>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: "#a5d6ff" }}>
            {sampleJson}
          </pre>
        </div>
      </div>

      <div className="report-actions" style={{ justifyContent: "center", marginTop: 20, display: "flex", gap: "12px" }}>
        <button className="btn-primary" onClick={copySchema}>
          {copied ? "✓ Copied JSON Schema" : "Copy Output JSON Schema"}
        </button>
        <Link href="/media" className="btn-secondary">
          Run Live Investigation →
        </Link>
      </div>
    </div>
  );
}
