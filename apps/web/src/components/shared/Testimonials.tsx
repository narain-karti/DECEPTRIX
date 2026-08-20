export default function Testimonials() {
  const testimonials = [
    {
      text: "Saved us hours of manual fact-checking. The source extraction is incredibly precise.",
      author: "Sarah J.",
      role: "Lead Fact-Checker, TruthWire"
    },
    {
      text: "Finally, an investigation tool that provides evidence instead of a black-box AI verdict.",
      author: "Michael T.",
      role: "Digital Forensics Analyst"
    },
    {
      text: "The C2PA provenance checks are seamlessly integrated. Crucial for our daily workflow.",
      author: "Elena R.",
      role: "Journalist, Global News"
    }
  ];

  return (
    <section className="section-gap" id="testimonials">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: 64 }}>
          <p className="section-label">TESTIMONIALS</p>
          <h2 className="h2">
            Trusted by<br />
            Great Investigators<span className="text-orange">.</span>
          </h2>
        </div>

        <div className="testimonials-grid">
          {testimonials.map((t, i) => (
            <div className="testimonial-card" key={i}>
              <div className="stars">★★★★★</div>
              <p className="testimonial-text">"{t.text}"</p>
              <div className="testimonial-author">
                <div className="author-avatar" />
                <div className="author-info">
                  <div>{t.author}</div>
                  <div>{t.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
