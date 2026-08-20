const cards = [
  {
    icon: "🔬",
    title: "Pixel Analysis",
    desc: "Frame-level manipulation detection using pinned, pretrained visual detectors with locked versions and documented limitations.",
    status: "Active",
    active: true,
  },
  {
    icon: "🎵",
    title: "Audio Analysis",
    desc: "Speech detection, language identification, and audio integrity checks. Deepfake voice detection is a future capability.",
    status: "Coming Soon",
    active: false,
  },
  {
    icon: "📋",
    title: "Metadata Inspection",
    desc: "Container format, codec, resolution, duration, creation dates, and stream integrity verified via ffprobe.",
    status: "Active",
    active: true,
  },
  {
    icon: "🔗",
    title: "Provenance / C2PA",
    desc: "Content credential verification. Absence is reported as informational — never treated as suspicious.",
    status: "Active",
    active: true,
  },
  {
    icon: "🧠",
    title: "Semantic Analysis",
    desc: "Advisory visual observations from frame batches. Remains advisory-only unless independently evaluated.",
    status: "Active",
    active: true,
  },
  {
    icon: "📚",
    title: "Source Verification",
    desc: "Official-first retrieval with 4-tier source policy. Primary authorities checked before discovery search.",
    status: "Active",
    active: true,
  },
];

export default function EvidenceCards() {
  return (
    <section className="services-section" id="services">
      <div className="section-label">SERVICES / EVIDENCE LAYERS</div>
      <h2 className="h2" style={{ maxWidth: 600 }}>
        What We Analyze.
      </h2>
      <p style={{ color: "rgba(255,255,255,0.6)", maxWidth: 600, marginTop: 12 }}>
        Each evidence type is analyzed independently and presented separately
        before any synthesis. No signal is hidden or averaged away.
      </p>

      <div className="services-grid">
        {cards.map((card, i) => (
          <div className="service-card" key={i}>
            <div className="service-icon">{card.icon}</div>
            <h4 className="service-title">{card.title}</h4>
            <p className="service-desc">{card.desc}</p>
            <div style={{ marginTop: "auto" }}>
               {card.active ? (
                 <span className="pill-outline" style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white" }}>
                   Active
                 </span>
               ) : (
                 <span className="pill-outline" style={{ background: "transparent", borderColor: "rgba(255,255,255,0.2)", color: "rgba(255,255,255,0.5)" }}>
                   Coming Soon
                 </span>
               )}
            </div>
            <div style={{ position: "absolute", bottom: 24, right: 24, opacity: 0.5 }}>
              →
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
