const steps = [
  { icon: "📤", title: "Upload", desc: "Submit video or paste text claim" },
  { icon: "✅", title: "Validate", desc: "Type, size, format, integrity checks" },
  { icon: "🎞️", title: "Extract", desc: "Frames, audio, metadata, atomic claims" },
  { icon: "🔬", title: "Analyze", desc: "Detectors, source retrieval, signals" },
  { icon: "🔗", title: "Provenance", desc: "C2PA, hashing, origin checks" },
  { icon: "⚖️", title: "Fuse", desc: "Evidence synthesis, disagreement flags" },
  { icon: "📄", title: "Report", desc: "Auditable JSON + HTML with limitations" },
];

export default function PipelineSection() {
  return (
    <section className="pipeline-section section-gap" id="pipeline">
      <div className="container">
        <div className="pipeline-header">
          <p className="overline">How It Works</p>
          <h2 className="h2">
            Seven-stage evidence <span className="accent">pipeline</span>
          </h2>
          <p>
            Every investigation follows the same structured path — from intake
            to auditable report. No shortcuts, no hidden decisions.
          </p>
        </div>

        <div className="pipeline-steps">
          {steps.map((step, i) => (
            <div className="pipeline-step" key={i}>
              <div className="pipeline-icon">
                <span>{step.icon}</span>
              </div>
              <div className="pipeline-step-title">{step.title}</div>
              <div className="pipeline-step-desc">{step.desc}</div>
              {i < steps.length - 1 && (
                <div className="pipeline-connector" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
