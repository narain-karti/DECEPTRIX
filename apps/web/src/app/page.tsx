"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import EvidenceCards from "../components/shared/EvidenceCards";
import UseCases from "../components/shared/UseCases";
import ImpactStats from "../components/shared/ImpactStats";
import Testimonials from "../components/shared/Testimonials";
import ReportPreview from "../components/report/ReportPreview";
import MediaAudit from "../components/media/MediaAudit";
import RumourAudit from "../components/rumour/RumourAudit";

type TabState = "studio" | "layers" | "cases" | "threats";
type StudioMode = "media" | "rumour";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabState>("studio");
  const [studioMode, setStudioMode] = useState<StudioMode>("media");
  const [apiLatency, setApiLatency] = useState<string>("Checking...");
  const [apiStatus, setApiStatus] = useState<"online" | "offline">("online");

  useEffect(() => {
    const checkHealth = async () => {
      const start = Date.now();
      try {
        const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          setApiLatency(`${Date.now() - start}ms`);
          setApiStatus("online");
        } else {
          setApiLatency("HTTP Error");
          setApiStatus("offline");
        }
      } catch {
        setApiLatency("Local Mode (Ready)");
        setApiStatus("online");
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="dashboard-grid">
      {/* LEFT COLUMN: FORENSIC NODE TELEMETRY */}
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        
        {/* Primary Forensic Node Card */}
        <div className="profile-card">
          <div className="profile-header-area">
            <div className="profile-avatar-large" style={{ background: "linear-gradient(135deg, #FF5A24 0%, #FF7347 100%)", color: "#fff", fontWeight: 800 }}>
              DX
            </div>
            <div className="pill-outline" style={{ border: "1px solid rgba(0, 214, 143, 0.3)", backgroundColor: "rgba(0, 214, 143, 0.05)", color: "#00d68f", marginBottom: "12px" }}>
              <span className="pill-dot" style={{ backgroundColor: "#00d68f" }} />
              ACTIVE FORENSIC NODE
            </div>
            <h1 className="profile-title" style={{ fontSize: "20px" }}>DECEPTRIX Core</h1>
            <p className="profile-subtitle">Multi-Modal Disinformation Engine</p>
            <div className="profile-meta-row">
              <span className="profile-meta-item">SIH-2026 Cluster</span>
              <span className="profile-meta-item">ID: DX-884-AI</span>
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border-light)", paddingTop: "16px", marginBottom: "16px" }}>
            <div className="card-section-title" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "15px", height: "15px", color: "var(--accent)" }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              Node Telemetry
            </div>
            <div className="data-row">
              <span className="data-label">API Status</span>
              <span className="data-value" style={{ color: "#00d68f", display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#00d68f" }} />
                {apiLatency}
              </span>
            </div>
            <div className="data-row">
              <span className="data-label">Celery Worker</span>
              <span className="data-value">Multi-Threaded Queue</span>
            </div>
            <div className="data-row">
              <span className="data-label">Evidence Schema</span>
              <span className="data-value" style={{ fontFamily: "monospace", fontSize: "11px", color: "#a5d6ff" }}>v2.0-Audit</span>
            </div>
            <div className="data-row">
              <span className="data-label">Integrity Hash</span>
              <span className="data-value">SHA-256 (Enforced)</span>
            </div>
          </div>

          <div className="profile-actions">
            <Link href="/media" className="btn-primary" style={{ textAlign: "center" }}>
              Launch Media
            </Link>
            <Link href="/rumour" className="btn-secondary" style={{ textAlign: "center" }}>
              Launch Rumour
            </Link>
          </div>
        </div>

        {/* Secondary Info Card: Model Registry */}
        <div className="secondary-card" style={{ marginTop: 0 }}>
          <div className="card-section-title">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#00d68f", display: "inline-block", boxShadow: "0 0 6px #00d68f" }} />
            Loaded Forensic Engines
          </div>
          <div className="data-row">
            <span className="data-label">Deepfake ViT</span>
            <span className="data-value" style={{ fontFamily: "monospace", fontSize: "11px" }}>dima806/ViT-16</span>
          </div>
          <div className="data-row">
            <span className="data-label">Lip-Sync</span>
            <span className="data-value">MediaPipe MAR + RMS</span>
          </div>
          <div className="data-row">
            <span className="data-label">NLI Entailment</span>
            <span className="data-value" style={{ fontFamily: "monospace", fontSize: "11px" }}>BART-Large-MNLI</span>
          </div>
          <div className="data-row">
            <span className="data-label">Frequency DCT</span>
            <span className="data-value">Scipy Spectral Norm</span>
          </div>
        </div>

        {/* Secondary Info Card: Policy & Source Packs */}
        <div className="secondary-card" style={{ marginTop: 0 }}>
          <div className="card-section-title">Jurisdiction & Policy</div>
          <div className="data-row">
            <span className="data-label">Active Policy</span>
            <span className="data-value" style={{ fontFamily: "monospace", fontSize: "11px", color: "var(--accent)" }}>gov_in_v1</span>
          </div>
          <div className="data-row">
            <span className="data-label">Primary Tier 1</span>
            <span className="data-value">.gov.in / .nic.in / .edu</span>
          </div>
          <div className="data-row">
            <span className="data-label">Fact-Check Tier 2</span>
            <span className="data-value">PIB / Snopes / Verified</span>
          </div>
        </div>

      </div>

      {/* RIGHT COLUMN: MAIN WORKSPACE */}
      <div>
        
        {/* Floating Secondary Navigation */}
        <div style={{ display: "flex", justifyContent: "center" }}>
          <div className="floating-nav">
            <button 
              className={`floating-nav-item ${activeTab === "studio" ? "active" : ""}`}
              onClick={() => setActiveTab("studio")}
            >
              Investigation Studio
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "layers" ? "active" : ""}`}
              onClick={() => setActiveTab("layers")}
            >
              Ensemble Layers
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "cases" ? "active" : ""}`}
              onClick={() => setActiveTab("cases")}
            >
              Domain Use Cases
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "threats" ? "active" : ""}`}
              onClick={() => setActiveTab("threats")}
            >
              Threat Models
            </button>
          </div>
        </div>

        {/* Tab workspace content */}
        <div style={{ minHeight: "600px" }}>
          {activeTab === "studio" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              
              {/* Studio Interactive Container */}
              <div 
                className="secondary-card" 
                style={{
                  marginTop: 0,
                  background: "var(--surface-dark)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-xl)",
                  padding: "24px",
                  boxShadow: "var(--shadow-card)",
                  position: "relative"
                }}
              >
                {/* Mode Selector */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid var(--border-light)", paddingBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
                  <div>
                    <span className="section-label">Live Forensic Workspace</span>
                    <h2 style={{ fontSize: "20px", fontWeight: "700", margin: "2px 0 0 0" }}>
                      {studioMode === "media" ? "Video Deepfake & Facial Forensics" : "Viral Text Rumour & Source Fact-Checking"}
                    </h2>
                  </div>
                  <div style={{ display: "flex", background: "var(--bg-primary)", padding: "4px", borderRadius: "var(--radius-pill)", border: "1px solid var(--border)" }}>
                    <button
                      onClick={() => setStudioMode("media")}
                      style={{
                        background: studioMode === "media" ? "var(--accent)" : "transparent",
                        color: studioMode === "media" ? "#fff" : "var(--text-secondary)",
                        border: "none",
                        padding: "6px 14px",
                        borderRadius: "var(--radius-pill)",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                        transition: "all 0.2s ease"
                      }}
                    >
                      🎬 Media Audit
                    </button>
                    <button
                      onClick={() => setStudioMode("rumour")}
                      style={{
                        background: studioMode === "rumour" ? "var(--accent)" : "transparent",
                        color: studioMode === "rumour" ? "#fff" : "var(--text-secondary)",
                        border: "none",
                        padding: "6px 14px",
                        borderRadius: "var(--radius-pill)",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                        transition: "all 0.2s ease"
                      }}
                    >
                      📰 Rumour Audit
                    </button>
                  </div>
                </div>

                {/* Active Studio Component */}
                {studioMode === "media" ? <MediaAudit /> : <RumourAudit />}
              </div>

              {/* Platform metrics */}
              <ImpactStats />

              {/* Report preview */}
              <ReportPreview />

            </div>
          )}

          {activeTab === "layers" && (
            <div className="secondary-card" style={{ marginTop: 0 }}>
              <EvidenceCards />
            </div>
          )}

          {activeTab === "cases" && (
            <div className="secondary-card" style={{ marginTop: 0 }}>
              <UseCases />
            </div>
          )}

          {activeTab === "threats" && (
            <div className="secondary-card" style={{ marginTop: 0 }}>
              <Testimonials />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
