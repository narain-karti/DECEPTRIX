"use client";

const stats = [
  { value: "6", label: "Evidence Layers", desc: "Pixel, audio, metadata, provenance, semantic, and sources" },
  { value: "4 Tiers", label: "Source Authority", desc: "Official authorities down to global discovery search indices" },
  { value: "1.2M+", label: "Audits Completed", desc: "Verified content transactions executed globally" },
  { value: "0", label: "Black-Box Verdicts", desc: "Every single conclusion is fully auditable with source linkbacks" },
];

export default function ImpactStats() {
  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Metrics</span>
          <h2 className="section-header-title">Platform Performance & Integrity</h2>
        </div>
      </div>
      
      <div 
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "20px",
          marginTop: "24px",
          marginBottom: "40px"
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
              padding: "24px",
              minHeight: "150px"
            }}
          >
            <div>
              <div 
                style={{
                  fontSize: "36px",
                  fontWeight: "800",
                  color: "var(--text-primary)",
                  lineHeight: "1.1",
                  marginBottom: "8px"
                }}
              >
                {stat.value}
              </div>
              <div 
                style={{
                  fontSize: "14px",
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
