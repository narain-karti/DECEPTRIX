"use client";

import { useState } from "react";
import Link from "next/link";
import EvidenceCards from "../components/shared/EvidenceCards";
import UseCases from "../components/shared/UseCases";
import ImpactStats from "../components/shared/ImpactStats";
import Testimonials from "../components/shared/Testimonials";
import ReportPreview from "../components/report/ReportPreview";

type TabState = "overview" | "layers" | "cases" | "testimonials";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabState>("overview");

  return (
    <div className="dashboard-grid">
      {/* LEFT COLUMN: PRIMARY PROFILE & INFO CARDS */}
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        {/* Profile / Primary Information Card */}
        <div className="profile-card">
          <div className="profile-header-area">
            <div className="profile-avatar-large">K</div>
            <div className="pill-outline" style={{ border: "1px solid rgba(0, 214, 143, 0.3)", backgroundColor: "rgba(0, 214, 143, 0.05)", color: "#00d68f", marginBottom: "12px" }}>
              <span className="pill-dot" style={{ backgroundColor: "#00d68f" }} />
              ACTIVE INVESTIGATOR
            </div>
            <h1 className="profile-title">Karthi Narain</h1>
            <p className="profile-subtitle">Lead Forensic Architect</p>
            <div className="profile-meta-row">
              <span className="profile-meta-item">New Delhi, IN</span>
              <span className="profile-meta-item">ID: 884-DX</span>
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border-light)", paddingTop: "20px", marginBottom: "20px" }}>
            <div className="card-section-title">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" style={{ width: "16px", height: "16px" }}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              Investigator Profile
            </div>
            <div className="data-row">
              <span className="data-label">Security Clearance</span>
              <span className="data-value">Level 4 (Authoritative)</span>
            </div>
            <div className="data-row">
              <span className="data-label">Total Investigations</span>
              <span className="data-value">1,248 cases</span>
            </div>
            <div className="data-row">
              <span className="data-label">Organization</span>
              <span className="data-value">Deceptrix Core Team</span>
            </div>
          </div>

          <div className="profile-actions">
            <button className="btn-secondary" onClick={() => alert("Node key copied to clipboard!")}>
              Copy Node ID
            </button>
            <button className="btn-primary" onClick={() => alert("Profile edits are locked by administrator.")}>
              Edit Profile
            </button>
          </div>
        </div>

        {/* Secondary Info Card: System Status */}
        <div className="secondary-card" style={{ marginTop: 0 }}>
          <div className="card-section-title">
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#00d68f", display: "inline-block", boxShadow: "0 0 6px #00d68f" }} />
            Node Operations
          </div>
          <div className="data-row">
            <span className="data-label">Local Pipeline</span>
            <span className="data-value" style={{ color: "#00d68f" }}>Operational</span>
          </div>
          <div className="data-row">
            <span className="data-label">Connected Peers</span>
            <span className="data-value">14 Nodes</span>
          </div>
          <div className="data-row">
            <span className="data-label">Default Policy Pack</span>
            <span className="data-value" style={{ fontFamily: "monospace", fontSize: "12px" }}>gov_in_v1</span>
          </div>
          <div className="data-row">
            <span className="data-label">Last Synchronization</span>
            <span className="data-value">2 mins ago</span>
          </div>
        </div>

        {/* Secondary Info Card: Subscription */}
        <div className="secondary-card" style={{ marginTop: 0 }}>
          <div className="card-section-title">Billing & License</div>
          <div className="data-row">
            <span className="data-label">License Type</span>
            <span className="data-value">Enterprise Pro Plan</span>
          </div>
          <div className="data-row">
            <span className="data-label">Usage Quota</span>
            <span className="data-value">12.4% (1,248 / 10,000)</span>
          </div>
          <div className="data-row">
            <span className="data-label">Renewal Date</span>
            <span className="data-value">Dec 30, 2026</span>
          </div>
        </div>

      </div>

      {/* RIGHT COLUMN: MAIN WORKSPACE */}
      <div>
        
        {/* Floating Secondary Navigation */}
        <div style={{ display: "flex", justifyContent: "center" }}>
          <div className="floating-nav">
            <button 
              className={`floating-nav-item ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              Overview
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "layers" ? "active" : ""}`}
              onClick={() => setActiveTab("layers")}
            >
              Evidence Layers
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "cases" ? "active" : ""}`}
              onClick={() => setActiveTab("cases")}
            >
              Use Cases
            </button>
            <button 
              className={`floating-nav-item ${activeTab === "testimonials" ? "active" : ""}`}
              onClick={() => setActiveTab("testimonials")}
            >
              Testimonials
            </button>
          </div>
        </div>

        {/* Tab workspace content */}
        <div style={{ minHeight: "600px" }}>
          {activeTab === "overview" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
              
              {/* Welcome banner */}
              <div 
                className="secondary-card" 
                style={{
                  marginTop: 0,
                  background: "linear-gradient(135deg, #111112 0%, #151617 100%)",
                  position: "relative",
                  overflow: "hidden"
                }}
              >
                <div style={{ position: "absolute", top: "-20px", right: "-20px", fontSize: "120px", opacity: 0.05, transform: "rotate(-15deg)", pointerEvents: "none" }}>
                  🛡️
                </div>
                <span className="section-label">Trust Infrastructure</span>
                <h2 style={{ fontSize: "28px", fontWeight: "700", marginBottom: "12px", marginTop: "4px" }}>
                  Investigate claims and media with verifiable evidence.
                </h2>
                <p style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.6", maxWidth: "640px", marginBottom: "24px" }}>
                  DECEPTRIX implements an evidence-first architecture that analyzes social media rumors and media files, exposes limitations, and generates transparent, auditable report artifacts.
                </p>
                
                {/* Launch buttons */}
                <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                  <Link href="/media" className="btn-primary" style={{ minWidth: "160px" }}>
                    Start Media Audit <span className="btn-arrow">→</span>
                  </Link>
                  <Link href="/rumour" className="btn-secondary" style={{ minWidth: "160px" }}>
                    Start Rumour Audit <span className="btn-arrow">→</span>
                  </Link>
                </div>
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

          {activeTab === "testimonials" && (
            <div className="secondary-card" style={{ marginTop: 0 }}>
              <Testimonials />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
