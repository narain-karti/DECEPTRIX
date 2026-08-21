"use client";

const threatModels = [
  {
    category: "SYNTHETIC FACIAL GENERATION",
    title: "Deepfake & FaceSwap Synthesis",
    desc: "Detects generative boundary blending, resolution mismatches between head and background, and facial patch-level artifacts using ViT Patch-16.",
    benchmark: "94.8% Detection Precision",
    level: "High Risk Tier",
    badgeColor: "#ff4d4d",
    icon: "🎭"
  },
  {
    category: "AUDIO-VISUAL REPLACEMENT",
    title: "Voice Cloning & Lip De-synchronization",
    desc: "Correlates Mouth Aspect Ratio (MAR) speech aperture dynamics against vocal acoustic energy (RMS) to identify synthetic dubbing.",
    benchmark: "0.067s Latency Tolerance",
    level: "High Risk Tier",
    badgeColor: "#ff4d4d",
    icon: "🎙️"
  },
  {
    category: "SPECTRAL GAN ARTIFACTS",
    title: "Frequency-Domain Grid Inconsistencies",
    desc: "Isolates high-frequency spectral spikes via 2D Discrete Cosine Transform (DCT) that escape human visual perception.",
    benchmark: "Sub-pixel Spectral Analysis",
    level: "Medium Risk Tier",
    badgeColor: "#ffaa00",
    icon: "⚡"
  },
  {
    category: "INFORMATIONAL FABRICATION",
    title: "Viral Text Rumour Disinformation",
    desc: "Deconstructs viral forwarded messages into discrete claims, cross-matching against Tier 1-4 official authorities with BART NLI entailment.",
    benchmark: "Live Multi-Tier Indexing",
    level: "Systemic Risk Tier",
    badgeColor: "#ff5a24",
    icon: "📰"
  }
];

export default function Testimonials() {
  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Threat Landscape</span>
          <h2 className="section-header-title">Evaluated Threat Models & Benchmarks</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "680px" }}>
        DECEPTRIX targets specific manipulation vectors spanning generative neural models, acoustic voice clones, and synthetic text disinformation.
      </p>

      <div 
        style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", 
          gap: "16px",
          marginTop: "16px" 
        }}
      >
        {threatModels.map((t, i) => (
          <div 
            className="secondary-card" 
            key={i}
            style={{ 
              marginTop: 0, 
              padding: "20px", 
              display: "flex", 
              flexDirection: "column", 
              justifyContent: "space-between",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)"
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <span style={{ fontSize: "24px" }}>{t.icon}</span>
                <span 
                  className="tier-badge" 
                  style={{ 
                    background: `${t.badgeColor}15`, 
                    color: t.badgeColor, 
                    fontSize: "10px", 
                    fontWeight: 700 
                  }}
                >
                  {t.level}
                </span>
              </div>
              <div className="caption" style={{ color: "var(--accent)", fontSize: "11px", fontWeight: 700, marginBottom: "4px" }}>
                {t.category}
              </div>
              <h4 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "8px", color: "var(--text-primary)" }}>
                {t.title}
              </h4>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "16px" }}>
                {t.desc}
              </p>
            </div>
            
            <div style={{ borderTop: "1px solid var(--border-light)", paddingTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="caption" style={{ fontSize: "11px" }}>Benchmark Target</span>
              <span style={{ fontSize: "12px", fontWeight: 600, color: "#a5d6ff", fontFamily: "monospace" }}>{t.benchmark}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
