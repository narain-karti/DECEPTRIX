"use client";

const testimonials = [
  {
    text: "Saved us hours of manual fact-checking. The source extraction is incredibly precise.",
    author: "Sarah J.",
    role: "Lead Fact-Checker, TruthWire",
    avatar: "S"
  },
  {
    text: "Finally, an investigation tool that provides evidence instead of a black-box AI verdict.",
    author: "Michael T.",
    role: "Digital Forensics Analyst",
    avatar: "M"
  },
  {
    text: "The C2PA provenance checks are seamlessly integrated. Crucial for our daily workflow.",
    author: "Elena R.",
    role: "Journalist, Global News",
    avatar: "E"
  }
];

export default function Testimonials() {
  return (
    <div>
      <div className="section-header-row">
        <div>
          <span className="section-label">Trust</span>
          <h2 className="section-header-title">Trusted by Forensics & Media Teams</h2>
        </div>
      </div>

      <div className="testimonials-grid" style={{ marginTop: "24px" }}>
        {testimonials.map((t, i) => (
          <div className="testimonial-card" key={i}>
            <div style={{ color: "var(--accent)", fontSize: "16px", marginBottom: "12px" }}>
              ★★★★★
            </div>
            <p className="testimonial-text">"{t.text}"</p>
            <div className="testimonial-author">
              <div className="author-avatar">{t.avatar}</div>
              <div className="author-info">
                <div className="author-name">{t.author}</div>
                <div className="author-role">{t.role}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
