"use client";

import { useState } from "react";

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

const pastelClasses = [
  "card-pastel-3", // blue
  "card-pastel-2", // lavender
  "card-pastel-4", // green
  "card-pastel-1", // cream
  "card-pastel-5", // peach
  "card-pastel-6", // yellow
];

export default function EvidenceCards() {
  const [activeMenu, setActiveMenu] = useState<number | null>(null);

  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Analysis Layers</span>
          <h2 className="section-header-title">Evidence Analysis Layers</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "600px" }}>
        Each evidence type is analyzed independently and presented separately
        before any synthesis. No signal is hidden or averaged away.
      </p>

      <div className="content-grid grid-4">
        {cards.map((card, i) => (
          <div className="content-card" key={i}>
            {/* Zone 1: Pastel visual area */}
            <div className={`content-card-visual ${pastelClasses[i % pastelClasses.length]}`}>
              <span style={{ fontSize: "40px" }}>{card.icon}</span>
              <div 
                className="three-dot-menu" 
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveMenu(activeMenu === i ? null : i);
                }}
              >
                ⋮
              </div>
              
              {activeMenu === i && (
                <div 
                  style={{
                    position: "absolute",
                    top: "40px",
                    right: "12px",
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px 0",
                    boxShadow: "var(--shadow-popup)",
                    zIndex: 10,
                    width: "120px",
                  }}
                  onMouseLeave={() => setActiveMenu(null)}
                >
                  <div 
                    style={{ padding: "6px 12px", fontSize: "12px", color: "var(--text-primary)", cursor: "pointer" }}
                    onClick={() => alert(`Opening details for ${card.title}`)}
                  >
                    View Specs
                  </div>
                  <div 
                    style={{ padding: "6px 12px", fontSize: "12px", color: "var(--text-secondary)", cursor: "pointer" }}
                    onClick={() => alert(`API keys configuration for ${card.title}`)}
                  >
                    Config API
                  </div>
                </div>
              )}
            </div>

            {/* Zone 2: Information area */}
            <div className="content-card-info">
              <div>
                <h4 className="content-card-title">{card.title}</h4>
                <p className="content-card-desc">{card.desc}</p>
              </div>
              <div className="content-card-meta">
                <span>{card.status}</span>
                {card.active ? (
                  <span style={{ color: "#00d68f", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#00d68f" }} />
                    Online
                  </span>
                ) : (
                  <span style={{ color: "var(--text-muted)", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "var(--text-muted)" }} />
                    Idle
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
