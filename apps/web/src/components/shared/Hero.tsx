import Link from "next/link";

export default function Hero() {
  return (
    <section className="hero" id="hero">
      <div className="container">
        <div className="hero-content">
          <div>
            <div className="pill-outline" style={{ marginBottom: 24 }}>
              <div className="pill-dot" />
              LIVE INVESTIGATION PLATFORM
            </div>
            <h1 className="display hero-headline">
              Investigate
              <br />
              Deception with
              <br />
              <span className="text-orange">Evidence.</span>
            </h1>
            <p className="hero-sub">
              DECEPTRIX collects independent technical and source-based evidence,
              exposes limitations, and produces auditable reports — never a
              black-box verdict.
            </p>
            <div className="hero-actions">
              <Link href="/media" className="btn-primary">
                Start Audit
                <span className="btn-arrow">→</span>
              </Link>
              <Link href="/#services" className="btn-secondary">
                See How It Works <span style={{ marginLeft: 6 }}>→</span>
              </Link>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-circle"></div>
            <div className="hero-image">
              <img 
                src="https://images.unsplash.com/photo-1573164713988-8665fc963095?q=80&w=600&auto=format&fit=crop" 
                alt="Investigator profile" 
                style={{ width: "100%", maxWidth: 440, display: "block" }} 
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
