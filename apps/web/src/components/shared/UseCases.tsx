"use client";

import { useState } from "react";

const projects = [
  {
    icon: "🏛️",
    title: "Government",
    desc: "Triage misinformation about schemes, regulations, and advisories.",
    category: "PUBLIC SECTOR"
  },
  {
    icon: "📰",
    title: "Newsrooms & NGOs",
    desc: "Create research cases from images, clips, or viral claims.",
    category: "JOURNALISM"
  },
  {
    icon: "🎓",
    title: "Education",
    desc: "Teach media literacy through evidence and provenance exercises.",
    category: "ACADEMIA"
  },
  {
    icon: "💼",
    title: "Enterprise Security",
    desc: "Investigate executive impersonation and synthetic voice/video.",
    category: "CORPORATE"
  },
  {
    icon: "🛒",
    title: "Marketplaces",
    desc: "Pre-upload risk warning for manipulated seller media.",
    category: "E-COMMERCE"
  },
  {
    icon: "🏥",
    title: "Disaster & Health",
    desc: "Identify recycled visuals and unsupported emergency claims.",
    category: "CRISIS RESPONSE"
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
  const [activeMenu, setActiveMenu] = useState<number | null>(null);

  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Featured Work</span>
          <h2 className="section-header-title">Domain Applications</h2>
        </div>
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px", maxWidth: "600px" }}>
        DECEPTRIX is deployed across diverse ecosystems to establish digital trust and analyze structural manipulation.
      </p>

      <div className="content-grid grid-4">
        {projects.map((project, i) => (
          <div className="content-card" key={i}>
            {/* Zone 1: Pastel visual area */}
            <div className={`content-card-visual ${pastelClasses[i % pastelClasses.length]}`}>
              <span style={{ fontSize: "40px" }}>{project.icon}</span>
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
                    onClick={() => alert(`Launching case study for ${project.title}`)}
                  >
                    Case Study
                  </div>
                  <div 
                    style={{ padding: "6px 12px", fontSize: "12px", color: "var(--text-secondary)", cursor: "pointer" }}
                    onClick={() => alert(`View API integration guide for ${project.title}`)}
                  >
                    API Docs
                  </div>
                </div>
              )}
            </div>

            {/* Zone 2: Information area */}
            <div className="content-card-info">
              <div>
                <h4 className="content-card-title">{project.title}</h4>
                <p className="content-card-desc">{project.desc}</p>
              </div>
              <div className="content-card-meta">
                <span style={{ color: "var(--accent)", fontSize: "10px", fontWeight: "700" }}>{project.category}</span>
                <span style={{ cursor: "pointer", color: "var(--text-secondary)" }} onClick={() => alert(`View application: ${project.title}`)}>
                  →
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
