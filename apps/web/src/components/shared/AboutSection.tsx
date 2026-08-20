export default function AboutSection() {
  return (
    <section className="organic-section" id="about">
      <div className="container">
        <div className="organic-container">
          {/* Structural branding notch */}
          <div className="organic-notch">D</div>

          <div className="organic-grid" style={{ marginTop: 48 }}>
            <div className="organic-image-placeholder">
              <span>🔬</span>
            </div>

            <div className="organic-text">
              <p className="overline">About the Platform</p>
              <h2 className="h2">
                Evidence infrastructure
                <br />
                for digital trust
              </h2>
              <p>
                DECEPTRIX is an evidence-first trust platform for investigating
                suspicious media and social-media rumours. It gives you two clear
                tools: <strong>Media Audit</strong> for short videos and{" "}
                <strong>Rumour Audit</strong> for pasted claims — producing
                auditable reports with every limitation disclosed.
              </p>
            </div>
          </div>

          {/* Dark + Lime cards */}
          <div className="organic-cards">
            <div className="organic-card-dark">
              <h4 className="h4">What We Analyze</h4>
              <ul>
                <li>
                  <span className="check">✓</span>
                  Pixel-level manipulation detection on video frames
                </li>
                <li>
                  <span className="check">✓</span>
                  Technical metadata &amp; file integrity inspection
                </li>
                <li>
                  <span className="check">✓</span>
                  Content provenance &amp; C2PA credential checks
                </li>
                <li>
                  <span className="check">✓</span>
                  Atomic claim extraction from forwarded messages
                </li>
                <li>
                  <span className="check">✓</span>
                  Official-first source retrieval &amp; verification
                </li>
                <li>
                  <span className="check">✓</span>
                  Multi-signal evidence fusion with disagreement flags
                </li>
              </ul>
            </div>

            <div className="organic-card-accent">
              <h4 className="h4">Why It Matters</h4>
              <div className="floating-tags">
                <span className="floating-tag">Evidence-First</span>
                <span className="floating-tag">Source Tiering</span>
                <span className="floating-tag">Audit Trail</span>
                <span className="floating-tag">Human Review</span>
                <span className="floating-tag">No Black Box</span>
                <span className="floating-tag">Inconclusive = Valid</span>
                <span className="floating-tag">Provenance</span>
                <span className="floating-tag">Explainable AI</span>
                <span className="floating-tag">Open Schema</span>
                <span className="floating-tag">Policy Governed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
