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

export default function UseCases() {
  return (
    <section className="section-gap" id="portfolio">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: 64 }}>
          <p className="section-label">FEATURED WORK / USE CASES</p>
          <h2 className="h2">
            Domain Applications<span className="text-orange">.</span>
          </h2>
        </div>

        <div className="portfolio-grid">
          {projects.map((project, i) => (
            <div className="project-card" key={i}>
              <div className="project-image" style={{ background: "var(--cream)" }}>
                {project.icon}
              </div>
              <div className="project-content">
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", marginBottom: 8, letterSpacing: "0.1em" }}>
                    {project.category}
                  </div>
                  <h3 className="h4" style={{ marginBottom: 4 }}>{project.title}</h3>
                  <p style={{ fontSize: 14, color: "rgba(32,33,31,0.7)" }}>{project.desc}</p>
                </div>
                <div className="btn-circular" style={{ flexShrink: 0, marginLeft: 16 }}>
                  →
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div style={{ textAlign: "center", marginTop: 48 }}>
          <a href="#" className="btn-primary">
            View All Domains <span className="btn-arrow">→</span>
          </a>
        </div>
      </div>
    </section>
  );
}
