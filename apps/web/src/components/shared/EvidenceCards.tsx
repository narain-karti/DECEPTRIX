"use client";

import { useState } from "react";

const cards = [
  {
    icon: "🔬",
    title: "ViT Deepfake Classifier",
    desc: "Vision Transformer binary classifier (dima806/ViT) scoring face crops for synthetic generative artifacts.",
    status: "Active (35% Weight)",
    active: true,
    model: "dima806/deepfake_vs_real_image_detection",
    specs: "Processes 224x224 RGB face crops. Evaluates patch-level generative artifacts, skin blending borders, and diffusion texture irregularities."
  },
  {
    icon: "👄",
    title: "Lip-Sync Correlation",
    desc: "Measures Mouth Aspect Ratio (MAR) against Librosa audio RMS power across 15 FPS temporal frame windows.",
    status: "Active (25% Weight)",
    active: true,
    model: "MediaPipe FaceMesh + Librosa RMS Pearson r",
    specs: "Calculates temporal synchronization between lip aperture dynamics and vocal energy envelope. Uncorrelated sequences indicate voiceover or audio replacement."
  },
  {
    icon: "👁️",
    title: "Facial Landmark Stability",
    desc: "Monitors 468 3D facial mesh points across temporal chunks to detect inter-ocular jitter and temporal flickering.",
    status: "Active (15% Weight)",
    active: true,
    model: "MediaPipe FaceMesh 468-point Tensor",
    specs: "Measures inter-ocular distance variance across consecutive frames. Deepfakes frequently suffer from frame-to-frame landmark micro-jitter."
  },
  {
    icon: "⚡",
    title: "2D-DCT Spectral Analysis",
    desc: "Discrete Cosine Transform frequency-domain inspection isolating anomalous high-frequency energy typical of GANs.",
    status: "Active (15% Weight)",
    active: true,
    model: "Scipy Orthogonal 2D-DCT",
    specs: "Analyzes radial frequency falloff in the face bounding box. Generative convolutional models exhibit characteristic high-frequency grid artifacts."
  },
  {
    icon: "📋",
    title: "Container & Stream Inspector",
    desc: "FFprobe container inspection verifying codecs, resolution, stream integrity, and creation timestamp tags.",
    status: "Active (10% Weight)",
    active: true,
    model: "FFprobe Stream Header & Tag Parser",
    specs: "Detects missing creation tags, non-standard re-encoding flags, stream duration discrepancies, and container tampering."
  },
  {
    icon: "📚",
    title: "4-Tier Source Fact-Checker",
    desc: "Retrieval pipeline cross-referencing text claims with authoritative public sources and NLI entailment.",
    status: "Active (NLI Verified)",
    active: true,
    model: "DuckDuckGo API + facebook/bart-large-mnli",
    specs: "Splits viral text into atomic assertions. Queries live indexes prioritizing Tier 1 (.gov, .edu) authorities and runs zero-shot entailment."
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
  const [selectedCard, setSelectedCard] = useState<typeof cards[0] | null>(null);

  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Ensemble Architecture</span>
          <h2 className="section-header-title">Multi-Signal Forensic Engines</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "680px" }}>
        Every investigation decomposes digital media into independent signal layers. 
        Each engine scores independently before Bayesian weighted fusion — preventing single-model bias.
      </p>

      <div className="content-grid grid-3" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
        {cards.map((card, i) => (
          <div 
            className="content-card" 
            key={i} 
            onClick={() => setSelectedCard(card)}
            style={{ cursor: "pointer", transition: "transform 0.2s ease, border-color 0.2s ease" }}
          >
            {/* Zone 1: Pastel visual area */}
            <div className={`content-card-visual ${pastelClasses[i % pastelClasses.length]}`}>
              <span style={{ fontSize: "36px" }}>{card.icon}</span>
              <span className="pill-outline" style={{ fontSize: "11px", background: "rgba(0,0,0,0.2)", border: "none", color: "#fff" }}>
                Details ↗
              </span>
            </div>

            {/* Zone 2: Information area */}
            <div className="content-card-info">
              <div>
                <h4 className="content-card-title">{card.title}</h4>
                <p className="content-card-desc" style={{ minHeight: "42px" }}>{card.desc}</p>
              </div>
              <div className="content-card-meta" style={{ borderTop: "1px solid var(--border-light)", paddingTop: "12px", marginTop: "8px" }}>
                <span style={{ color: "var(--accent)", fontSize: "11px", fontWeight: 600 }}>{card.status}</span>
                <span style={{ color: "#00d68f", display: "inline-flex", alignItems: "center", gap: "4px", fontSize: "11px" }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#00d68f" }} />
                  Online
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Specification Modal */}
      {selectedCard && (
        <div 
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(4px)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px"
          }}
          onClick={() => setSelectedCard(null)}
        >
          <div 
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "28px",
              maxWidth: "520px",
              width: "100%",
              boxShadow: "var(--shadow-popup)",
              position: "relative"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setSelectedCard(null)}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                fontSize: "18px",
                cursor: "pointer"
              }}
            >
              ✕
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <span style={{ fontSize: "36px" }}>{selectedCard.icon}</span>
              <div>
                <h3 className="h3" style={{ fontSize: "20px" }}>{selectedCard.title}</h3>
                <span style={{ color: "var(--accent)", fontSize: "12px", fontWeight: 600 }}>{selectedCard.status}</span>
              </div>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <div className="caption" style={{ marginBottom: "4px" }}>Model & Underlying Framework</div>
              <div style={{ fontFamily: "monospace", fontSize: "13px", color: "#a5d6ff", background: "rgba(0,0,0,0.3)", padding: "8px 12px", borderRadius: "var(--radius-sm)" }}>
                {selectedCard.model}
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <div className="caption" style={{ marginBottom: "4px" }}>Technical Execution Scope</div>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                {selectedCard.specs}
              </p>
            </div>

            <button className="btn-primary" style={{ width: "100%" }} onClick={() => setSelectedCard(null)}>
              Close Technical Spec
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
