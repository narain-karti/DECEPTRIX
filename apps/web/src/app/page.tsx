"use client";

import { useState } from "react";
import Link from "next/link";
import EvidenceCards from "../components/shared/EvidenceCards";
import UseCases from "../components/shared/UseCases";
import ImpactStats from "../components/shared/ImpactStats";
import Testimonials from "../components/shared/Testimonials";
import ReportPreview from "../components/report/ReportPreview";

type NavSection = "architecture" | "layers" | "threats" | "usecases" | "schema";

export default function Home() {
  const [activeSection, setActiveSection] = useState<NavSection>("architecture");
  const [selectedPipelineStep, setSelectedPipelineStep] = useState<number>(0);

  const pipelineStages = [
    {
      step: 1,
      title: "Intake & SHA-256 Fingerprint",
      shortTitle: "Intake",
      icon: "📥",
      desc: "Video file (MP4/WebM) or text rumor is received. Computes a chunked SHA-256 cryptographic digest immediately.",
      details: "Enforces MIME bounds, 200MB size limit, and UUID path sanitization. The SHA-256 hash becomes the immutable Case ID root."
    },
    {
      step: 2,
      title: "Stream & Keyframe Extraction",
      shortTitle: "Extraction",
      icon: "🎞️",
      desc: "FFmpeg extracts dense 15 FPS frame sequence and converts audio stream to 16,000 Hz mono PCM.",
      details: "Extracts container streams, frame timestamps, and codec headers. Detects missing creation timestamps or container tampering."
    },
    {
      step: 3,
      title: "5-Engine Parallel Neural Analysis",
      shortTitle: "Analysis",
      icon: "🔬",
      desc: "Dispatches frames, audio, and claims across 5 parallel machine learning and signal-processing models.",
      details: "Runs ViT Deepfake Classifier, MediaPipe 468-pt FaceMesh, Lip-Sync MAR vs. RMS correlation, 2D-DCT spectral analysis, and BART NLI entailment."
    },
    {
      step: 4,
      title: "Multi-Modal Bayesian Fusion",
      shortTitle: "Fusion",
      icon: "⚖️",
      desc: "Fuses all individual anomaly scores using a calibrated weighted ensemble (35% ViT, 25% Lip-Sync, 15% Jitter, 15% DCT, 10% Metadata).",
      details: "Disagreement flags are raised if visual and acoustic signals diverge. Generates an explainable composite risk score."
    },
    {
      step: 5,
      title: "Tamper-Evident Report Generation",
      shortTitle: "Reporting",
      icon: "📄",
      desc: "Outputs a court-ready PDF forensic audit report with embedded face crops and a cryptographically signed JSON record.",
      details: "Includes complete source citations, full limitations disclosures, keyframe timeline cards, and an immutable SHA-256 record signature."
    }
  ];

  return (
    <div style={{ maxWidth: "1140px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "32px" }}>
      
      {/* ── HERO BANNER ── */}
      <div 
        className="secondary-card" 
        style={{
          marginTop: 0,
          background: "linear-gradient(135deg, #131416 0%, #1c1d20 100%)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-xl)",
          padding: "36px",
          position: "relative",
          overflow: "hidden",
          boxShadow: "var(--shadow-card)"
        }}
      >
        <div style={{ position: "absolute", top: "-20px", right: "-20px", fontSize: "140px", opacity: 0.04, transform: "rotate(-15deg)", pointerEvents: "none" }}>
          🛡️
        </div>

        <div style={{ maxWidth: "780px" }}>
          <div className="pill-outline" style={{ border: "1px solid rgba(255, 90, 36, 0.3)", backgroundColor: "rgba(255, 90, 36, 0.08)", color: "var(--accent)", marginBottom: "16px", display: "inline-flex", alignItems: "center", gap: "8px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "var(--accent)" }} />
            EXPLAINABLE FORENSIC INFRASTRUCTURE · SIH 2026
          </div>

          <h1 style={{ fontSize: "36px", fontWeight: "800", lineHeight: "1.2", marginBottom: "14px", color: "var(--text-primary)" }}>
            Investigate Deception with <span className="text-orange">Verifiable Evidence.</span>
          </h1>

          <p style={{ color: "var(--text-secondary)", fontSize: "15px", lineHeight: "1.6", marginBottom: "28px" }}>
            DECEPTRIX decomposes viral media and forwarded social claims into transparent forensic signals. 
            Combining Vision Transformers, audio-visual lip synchrony, spectral frequency analysis, and 4-tier source entailment — with zero black-box decisions.
          </p>

          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
            <Link href="/media" className="btn-primary" style={{ padding: "12px 24px", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>🎬</span> Launch Media Audit <span className="btn-arrow">→</span>
            </Link>
            <Link href="/rumour" className="btn-secondary" style={{ padding: "12px 24px", fontSize: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>📰</span> Launch Rumour Audit <span className="btn-arrow">→</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ── INTERACTIVE EXPLAINER NAVIGATION TABS ── */}
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div className="floating-nav" style={{ flexWrap: "wrap", justifyContent: "center" }}>
          <button 
            className={`floating-nav-item ${activeSection === "architecture" ? "active" : ""}`}
            onClick={() => setActiveSection("architecture")}
          >
            Pipeline Flow
          </button>
          <button 
            className={`floating-nav-item ${activeSection === "layers" ? "active" : ""}`}
            onClick={() => setActiveSection("layers")}
          >
            5 Forensic Engines
          </button>
          <button 
            className={`floating-nav-item ${activeSection === "threats" ? "active" : ""}`}
            onClick={() => setActiveSection("threats")}
          >
            Threat Vectors
          </button>
          <button 
            className={`floating-nav-item ${activeSection === "usecases" ? "active" : ""}`}
            onClick={() => setActiveSection("usecases")}
          >
            Domain Use Cases
          </button>
          <button 
            className={`floating-nav-item ${activeSection === "schema" ? "active" : ""}`}
            onClick={() => setActiveSection("schema")}
          >
            Output Schema & PDF
          </button>
        </div>
      </div>

      {/* ── ACTIVE SECTION VIEW ── */}
      <div>
        {activeSection === "architecture" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
            
            {/* Interactive 5-Stage Architecture Flowchart */}
            <div className="secondary-card" style={{ marginTop: 0, padding: "32px", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)" }}>
              <div className="section-header-row">
                <div>
                  <span className="section-label">System Architecture</span>
                  <h2 className="section-header-title">End-to-End Multi-Modal Forensic Pipeline</h2>
                </div>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "28px", maxWidth: "700px" }}>
                Click any pipeline node below to explore how data flows from initial ingestion to cryptographic report generation.
              </p>

              {/* Step Node Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "12px", position: "relative" }}>
                {pipelineStages.map((st, i) => {
                  const isSelected = selectedPipelineStep === i;
                  return (
                    <div 
                      key={i}
                      onClick={() => setSelectedPipelineStep(i)}
                      style={{
                        background: isSelected ? "rgba(255, 90, 36, 0.12)" : "var(--bg-secondary)",
                        border: `2px solid ${isSelected ? "var(--accent)" : "var(--border)"}`,
                        borderRadius: "var(--radius-md)",
                        padding: "18px 14px",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        textAlign: "center",
                        position: "relative"
                      }}
                    >
                      <div style={{ fontSize: "28px", marginBottom: "8px" }}>{st.icon}</div>
                      <span style={{ fontSize: "11px", fontWeight: 700, color: isSelected ? "var(--accent)" : "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>
                        Stage 0{st.step}
                      </span>
                      <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                        {st.shortTitle}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Selected Stage Detail Inspector */}
              <div 
                style={{
                  marginTop: "24px",
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid var(--border-light)",
                  borderRadius: "var(--radius-lg)",
                  padding: "24px",
                  display: "flex",
                  gap: "20px",
                  alignItems: "flex-start",
                  flexWrap: "wrap"
                }}
              >
                <div style={{ fontSize: "36px", padding: "12px", background: "rgba(255, 90, 36, 0.1)", borderRadius: "var(--radius-md)", border: "1px solid rgba(255, 90, 36, 0.3)" }}>
                  {pipelineStages[selectedPipelineStep].icon}
                </div>
                <div style={{ flex: 1, minWidth: "260px" }}>
                  <div className="caption" style={{ color: "var(--accent)", fontWeight: 700 }}>
                    STAGE 0{pipelineStages[selectedPipelineStep].step} SPECIFICATION
                  </div>
                  <h3 style={{ fontSize: "18px", fontWeight: 700, margin: "4px 0 8px 0", color: "var(--text-primary)" }}>
                    {pipelineStages[selectedPipelineStep].title}
                  </h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.5", marginBottom: "12px" }}>
                    {pipelineStages[selectedPipelineStep].desc}
                  </p>
                  <div style={{ fontSize: "12px", color: "#a5d6ff", background: "rgba(165, 214, 255, 0.05)", padding: "10px 14px", borderRadius: "var(--radius-sm)", border: "1px solid rgba(165, 214, 255, 0.15)" }}>
                    <strong>Engine Details:</strong> {pipelineStages[selectedPipelineStep].details}
                  </div>
                </div>
              </div>

            </div>

            {/* Platform Metrics */}
            <ImpactStats />

            {/* Quick Action Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
              <div className="secondary-card" style={{ marginTop: 0, padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontSize: "32px", marginBottom: "12px" }}>🎬</div>
                  <h3 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>Media Deepfake Audit</h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", marginBottom: "20px" }}>
                    Upload MP4/WebM videos to perform dense 15 FPS keyframe extraction, ViT face classification, lip-sync audio correlation, and 2D-DCT frequency analysis.
                  </p>
                </div>
                <Link href="/media" className="btn-primary" style={{ textAlign: "center", display: "block" }}>
                  Open Media Audit Studio →
                </Link>
              </div>

              <div className="secondary-card" style={{ marginTop: 0, padding: "28px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontSize: "32px", marginBottom: "12px" }}>📰</div>
                  <h3 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>Rumour Fact-Checking</h3>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", marginBottom: "20px" }}>
                    Paste viral social messages to extract atomic claims, retrieve evidence from 4 source authority tiers, and compute BART-Large-MNLI entailment.
                  </p>
                </div>
                <Link href="/rumour" className="btn-secondary" style={{ textAlign: "center", display: "block" }}>
                  Open Rumour Audit Studio →
                </Link>
              </div>
            </div>

          </div>
        )}

        {activeSection === "layers" && (
          <div className="secondary-card" style={{ marginTop: 0, padding: "28px" }}>
            <EvidenceCards />
          </div>
        )}

        {activeSection === "threats" && (
          <div className="secondary-card" style={{ marginTop: 0, padding: "28px" }}>
            <Testimonials />
          </div>
        )}

        {activeSection === "usecases" && (
          <div className="secondary-card" style={{ marginTop: 0, padding: "28px" }}>
            <UseCases />
          </div>
        )}

        {activeSection === "schema" && (
          <div className="secondary-card" style={{ marginTop: 0, padding: "28px" }}>
            <ReportPreview />
          </div>
        )}
      </div>

    </div>
  );
}
