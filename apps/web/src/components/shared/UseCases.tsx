"use client";

import { useState } from "react";

const projects = [
  {
    icon: "🏛️",
    title: "Government & Regulatory",
    desc: "Triage public misinformation regarding official welfare schemes, statutory circulars, and national advisories.",
    category: "PUBLIC SECTOR",
    workflow: "Ingests viral social messages, matches against Tier 1 official Gazette & Ministry endpoints, and outputs tamper-evident public rebuttals."
  },
  {
    icon: "📰",
    title: "Newsrooms & Fact-Checkers",
    desc: "High-speed triage of breaking eyewitness footage and viral speech clips before publishing breaking news.",
    category: "JOURNALISM",
    workflow: "Runs spatio-temporal ViT frame scoring, extracts audio-visual lip-sync discrepancies, and generates traceable editorial citations."
  },
  {
    icon: "🎓",
    title: "Forensic Education & Academia",
    desc: "Demonstrate multi-signal AI forensics, artifact detection, and open evidence schemas for researchers.",
    category: "ACADEMIA",
    workflow: "Inspects raw DCT spectral plots, MediaPipe landmark confidence tensors, and zero-shot NLI entailment matrices."
  },
  {
    icon: "💼",
    title: "Enterprise & Brand Defense",
    desc: "Investigate executive voice clones, synthetic board meeting videos, and market manipulation attempts.",
    category: "CORPORATE",
    workflow: "Cross-checks executive footage against known biometric benchmarks and verifies container metadata authenticity."
  },
  {
    icon: "🛒",
    title: "Digital Marketplaces & KYC",
    desc: "Pre-upload risk screening for manipulated identity documents, product demo videos, and seller profiles.",
    category: "E-COMMERCE",
    workflow: "Detects digital face replacement (FaceSwap) and synthetic texture re-rendering in real-time onboarding pipelines."
  },
  {
    icon: "🏥",
    title: "Emergency & Disaster Relief",
    desc: "Filter recycled crisis visuals, synthetic weather footage, and false disaster casualty counts.",
    category: "CRISIS RESPONSE",
    workflow: "Extracts container creation timestamps and cross-references historical reverse-search indexes to detect recycled media."
  }
];

const pastelClasses = [
  "card-pastel-1", // cream
  "card-pastel-5", // peach
  "card-pastel-2", // lavender
  "card-pastel-6", // yellow
  "card-pastel-3", // blue
  "card-pastel-7", // pink
];

export default function UseCases() {
  const [selectedProject, setSelectedProject] = useState<typeof projects[0] | null>(null);

  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Operational Deployment</span>
          <h2 className="section-header-title">Domain Applications & Workflows</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "680px" }}>
        DECEPTRIX establishes reproducible digital trust across government agencies, high-tempo newsrooms, and enterprise security operations.
      </p>

      <div className="content-grid grid-3" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
        {projects.map((project, i) => (
          <div 
            className="content-card" 
            key={i}
            onClick={() => setSelectedProject(project)}
            style={{ cursor: "pointer", transition: "transform 0.2s ease, border-color 0.2s ease" }}
          >
            {/* Zone 1: Pastel visual area */}
            <div className={`content-card-visual ${pastelClasses[i % pastelClasses.length]}`}>
              <span style={{ fontSize: "36px" }}>{project.icon}</span>
              <span className="pill-outline" style={{ fontSize: "10px", background: "rgba(0,0,0,0.2)", border: "none", color: "#fff" }}>
                {project.category}
              </span>
            </div>

            {/* Zone 2: Information area */}
            <div className="content-card-info">
              <div>
                <h4 className="content-card-title">{project.title}</h4>
                <p className="content-card-desc" style={{ minHeight: "42px" }}>{project.desc}</p>
              </div>
              <div className="content-card-meta" style={{ borderTop: "1px solid var(--border-light)", paddingTop: "12px", marginTop: "8px" }}>
                <span style={{ color: "var(--accent)", fontSize: "11px", fontWeight: "700" }}>{project.category}</span>
                <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>View Workflow →</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Case Study Modal */}
      {selectedProject && (
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
          onClick={() => setSelectedProject(null)}
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
              onClick={() => setSelectedProject(null)}
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
              <span style={{ fontSize: "36px" }}>{selectedProject.icon}</span>
              <div>
                <h3 className="h3" style={{ fontSize: "20px" }}>{selectedProject.title}</h3>
                <span style={{ color: "var(--accent)", fontSize: "12px", fontWeight: 700 }}>{selectedProject.category}</span>
              </div>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <div className="caption" style={{ marginBottom: "4px" }}>Operational Problem Statement</div>
              <p style={{ fontSize: "13px", color: "var(--text-primary)", lineHeight: "1.5" }}>
                {selectedProject.desc}
              </p>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <div className="caption" style={{ marginBottom: "4px" }}>DECEPTRIX Automated Forensic Workflow</div>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-light)" }}>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", margin: 0 }}>
                  {selectedProject.workflow}
                </p>
              </div>
            </div>

            <button className="btn-primary" style={{ width: "100%" }} onClick={() => setSelectedProject(null)}>
              Close Workflow
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
