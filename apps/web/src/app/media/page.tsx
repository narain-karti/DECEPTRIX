import Navbar from "../../components/shared/Navbar";
import Footer from "../../components/shared/Footer";
import MediaAudit from "../../components/media/MediaAudit";

export default function MediaAuditPage() {
  return (
    <>
      <Navbar />
      <main style={{ paddingTop: 100, minHeight: "calc(100vh - 200px)" }}>
        <section className="container">
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <p className="section-label">Investigation Tool</p>
            <h1 className="h2">
              <span className="text-orange">Media</span> Audit
            </h1>
            <p style={{ color: "var(--text-muted)", maxWidth: 600, margin: "12px auto 0" }}>
              Upload a video to analyze frames for manipulation, check technical metadata, and verify provenance credentials.
            </p>
          </div>
          <div style={{ maxWidth: 800, margin: "0 auto", background: "white", border: "1px solid var(--border)", borderRadius: 24, padding: "40px", boxShadow: "0 12px 40px rgba(0,0,0,0.05)" }}>
            <MediaAudit />
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
