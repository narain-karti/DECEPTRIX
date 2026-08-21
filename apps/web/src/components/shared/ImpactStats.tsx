"use client";

const stats = [
  { value: "5 Engines", label: "Multi-Modal Ensemble", desc: "ViT Deepfake classifier, MAR Lip-Sync correlation, FaceMesh jitter, 2D-DCT, and FFprobe inspector" },
  { value: "4 Tiers", label: "Source Authority Hierarchy", desc: "Official Gazette and primary endpoints down to global live search discovery" },
  { value: "15 FPS", label: "Temporal Sampling Density", desc: "Uniform frame sequence dissection and 16kHz mono acoustic energy alignment" },
  { value: "0", label: "Black-Box Verdicts", desc: "Every single conclusion is fully auditable with source linkbacks, face crops, and SHA-256 hashes" },
];

export default function ImpactStats() {
  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Architecture Metrics</span>
          <h2 className="section-header-title">Platform Performance & Signal Integrity</h2>
        </div>
      </div>
      
      <div 
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
          marginTop: "16px",
          marginBottom: "24px"
        }}
      >
        {stats.map((stat, i) => (
          <div 
            key={i} 
            className="secondary-card"
            style={{
              marginTop: 0,
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              padding: "20px",
              minHeight: "140px",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)"
            }}
          >
            <div>
              <div 
                style={{
                  fontSize: "28px",
                  fontWeight: "800",
                  color: "var(--text-primary)",
                  lineHeight: "1.1",
                  marginBottom: "6px"
                }}
              >
                {stat.value}
              </div>
              <div 
                style={{
                  fontSize: "13px",
                  fontWeight: "600",
                  color: "var(--accent)",
                  marginBottom: "4px"
                }}
              >
                {stat.label}
              </div>
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              {stat.desc}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
