import Navbar from "../../components/shared/Navbar";
import Footer from "../../components/shared/Footer";
import RumourAudit from "../../components/rumour/RumourAudit";

export default function RumourAuditPage() {
  return (
    <>
      <Navbar />
      <main style={{ paddingTop: 100, minHeight: "calc(100vh - 200px)" }}>
        <section className="container">
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <p className="section-label">Investigation Tool</p>
            <h1 className="h2">
              <span className="text-orange">Rumour</span> Audit
            </h1>
            <p style={{ color: "var(--text-muted)", maxWidth: 600, margin: "12px auto 0" }}>
              Paste a text claim to extract atomic assertions, retrieve evidence from 4 tiers of sources, and fuse the results.
            </p>
          </div>
          <div style={{ maxWidth: 800, margin: "0 auto", background: "white", border: "1px solid var(--border)", borderRadius: 24, padding: "40px", boxShadow: "0 12px 40px rgba(0,0,0,0.05)" }}>
            <RumourAudit />
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
