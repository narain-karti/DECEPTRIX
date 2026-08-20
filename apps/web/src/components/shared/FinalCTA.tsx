export default function FinalCTA() {
  return (
    <section className="container">
      <div className="cta-block">
        <p className="section-label" style={{ color: "var(--dark)" }}>LET'S WORK TOGETHER</p>
        <h2 className="display" style={{ color: "var(--dark)", marginBottom: 40, marginTop: 16 }}>
          Have a project in mind?<br />
          Let's create something bold.
        </h2>
        <a href="/media" className="btn-dark">
          Let's Discuss Your Project <span className="btn-arrow" style={{ background: "var(--orange)", color: "var(--dark)" }}>→</span>
        </a>
      </div>
    </section>
  );
}
