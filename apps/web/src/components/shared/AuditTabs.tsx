import Link from "next/link";

export default function AuditTabs() {
  return (
    <section className="audit-section section-gap" id="audit">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <p className="overline">Investigation Tools</p>
          <h2 className="h2">
            Start your <span className="accent">audit</span>
          </h2>
          <p style={{ color: "#8a8a8a", maxWidth: 600, margin: "12px auto 0" }}>
            Choose the type of evidence you want to analyze.
          </p>
        </div>

        <div style={{ display: "flex", gap: 24, justifyContent: "center", flexWrap: "wrap" }}>
          <Link href="/media" className="audit-launch-card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎬</div>
            <h3 className="h3">Media Audit</h3>
            <p style={{ color: "#8a8a8a", marginTop: 8 }}>
              Upload a video clip. We extract frames, analyze pixels for manipulation, check technical metadata, and verify C2PA content credentials.
            </p>
            <div className="btn-primary" style={{ marginTop: 24, width: "fit-content" }}>
              Start Media Audit <span className="btn-arrow">→</span>
            </div>
          </Link>
          
          <Link href="/rumour" className="audit-launch-card">
            <div style={{ fontSize: 48, marginBottom: 16 }}>📝</div>
            <h3 className="h3">Rumour Audit</h3>
            <p style={{ color: "#8a8a8a", marginTop: 8 }}>
              Paste a text claim or forwarded message. We extract atomic claims, retrieve evidence from 4 tiers of sources, and fuse the results.
            </p>
            <div className="btn-primary" style={{ marginTop: 24, width: "fit-content" }}>
              Start Rumour Audit <span className="btn-arrow">→</span>
            </div>
          </Link>
        </div>
      </div>
    </section>
  );
}
