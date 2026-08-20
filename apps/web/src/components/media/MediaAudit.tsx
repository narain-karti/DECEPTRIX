"use client";
import { useState, useCallback, useEffect, useRef } from "react";

type FlowState = "upload" | "processing" | "results";

const STAGES = ["Validate", "Extract", "Analyze", "Provenance", "Fuse", "Report"];

const MOCK_KEYFRAMES = [
  { time: "0:03", status: "clean" },
  { time: "0:08", status: "clean" },
  { time: "0:15", status: "warning" },
  { time: "0:22", status: "clean" },
  { time: "0:31", status: "warning" },
  { time: "0:45", status: "clean" },
];

const MOCK_EVIDENCE = [
  {
    color: "#00d68f",
    title: "Visual Analysis — SBI Detector v2.1",
    desc: "No significant manipulation artifacts detected in 14 of 16 sampled frames. Frames at 0:15 and 0:31 show minor compression artifacts consistent with social-media re-encoding.",
    meta: ["Score: 0.12 (low risk)", "CPU inference", "Coverage: 85%"],
  },
  {
    color: "#00b4d8",
    title: "Technical Metadata",
    desc: "Container: MP4 (isom/iso2). Codec: H.264 High@L3.1. Resolution: 1080×1920. Duration: 48s. Creation date present in container header.",
    meta: ["ffprobe v6.1", "All streams verified"],
  },
  {
    color: "#8a8a8a",
    title: "Content Provenance (C2PA)",
    desc: "No C2PA content credentials found. This is informational — absence of credentials is not evidence of manipulation.",
    meta: ["Status: absent", "Not suspicious"],
  },
  {
    color: "#ffaa00",
    title: "Semantic Analysis (Advisory)",
    desc: "Visual content shows a public gathering with signage. No faces detected for deepfake analysis. Audio track contains background speech — language detection: Hindi.",
    meta: ["Advisory only", "Not evaluated for accuracy"],
  },
];

export default function MediaAudit() {
  const [flow, setFlow] = useState<FlowState>("upload");
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<{ name: string; size: string; type: string } | null>(null);
  const [stageIdx, setStageIdx] = useState(-1);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const simulateUpload = useCallback((name: string, sizeBytes: number, type: string) => {
    const sizeStr =
      sizeBytes > 1024 * 1024
        ? `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
        : `${(sizeBytes / 1024).toFixed(0)} KB`;
    setFile({ name, size: sizeStr, type });
  }, []);

  const startProcessing = () => {
    setFlow("processing");
    setStageIdx(0);
    setProgress(0);
  };

  useEffect(() => {
    if (flow !== "processing") return;
    if (stageIdx >= STAGES.length) {
      setFlow("results");
      return;
    }
    const dur = 800 + Math.random() * 600;
    const timer = setTimeout(() => {
      setStageIdx((p) => p + 1);
      setProgress(((stageIdx + 1) / STAGES.length) * 100);
    }, dur);
    return () => clearTimeout(timer);
  }, [flow, stageIdx]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) simulateUpload(f.name, f.size, f.type);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) simulateUpload(f.name, f.size, f.type);
  };

  const reset = () => {
    setFlow("upload");
    setFile(null);
    setStageIdx(-1);
    setProgress(0);
  };

  /* ------ UPLOAD STATE ------ */
  if (flow === "upload") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Upload Video</span>
        </div>

        <div
          className={`upload-zone${dragOver ? " dragover" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/webm,video/quicktime"
            style={{ display: "none" }}
            onChange={handleFileSelect}
          />
          <span className="upload-icon">🎬</span>
          <div className="upload-title">
            Drop your video here or <span className="accent">browse</span>
          </div>
          <div className="upload-subtitle">
            MP4, WebM, or MOV · Up to 60 seconds · Max 200 MB
          </div>
          <div className="upload-formats">
            <span className="pill-outline">.mp4</span>
            <span className="pill-outline">.webm</span>
            <span className="pill-outline">.mov</span>
          </div>
        </div>

        {file && (
          <>
            <div className="file-info">
              <div className="file-icon">🎥</div>
              <div className="file-details">
                <div className="file-name">{file.name}</div>
                <div className="file-meta">
                  <span>{file.size}</span>
                  <span>{file.type || "video/mp4"}</span>
                </div>
                <div className="file-hash">
                  SHA-256: a1b2c3d4e5f6...{Math.random().toString(36).slice(2, 10)}
                </div>
              </div>
              <button className="file-remove" onClick={() => setFile(null)}>
                ✕
              </button>
            </div>
            <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
              <button className="btn-primary" onClick={startProcessing}>
                Analyze Video <span className="btn-arrow">→</span>
              </button>
              <button className="btn-secondary" onClick={() => setFile(null)}>
                Remove
              </button>
            </div>
          </>
        )}

        <div style={{ marginTop: 32 }}>
          <p className="caption">
            ⚠️ By uploading, you accept that temporary processing occurs on our
            servers. Files are deleted after analysis. No content is used for
            model training.
          </p>
        </div>
      </div>
    );
  }

  /* ------ PROCESSING STATE ------ */
  if (flow === "processing") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Processing...</span>
        </div>

        {file && (
          <div className="file-info" style={{ marginBottom: 24 }}>
            <div className="file-icon">🎥</div>
            <div className="file-details">
              <div className="file-name">{file.name}</div>
              <div className="file-meta">
                <span>{file.size}</span>
              </div>
            </div>
          </div>
        )}

        <div className="progress-container">
          <div className="progress-stages">
            {STAGES.map((stage, i) => (
              <div
                className={`progress-stage${
                  i < stageIdx ? " completed" : i === stageIdx ? " active" : ""
                }`}
                key={i}
              >
                <div className="progress-dot">
                  {i < stageIdx ? "✓" : ""}
                </div>
                <div className="progress-stage-label">{stage}</div>
                {i < STAGES.length - 1 && (
                  <div className="progress-line">
                    <div
                      className="progress-line-fill"
                      style={{ width: i < stageIdx ? "100%" : "0%" }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="progress-bar-track" style={{ marginTop: 32 }}>
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="progress-status">
            <span className="progress-status-text">
              {stageIdx < STAGES.length
                ? `Running: ${STAGES[stageIdx]}...`
                : "Finalizing..."}
            </span>
            <span className="progress-status-percent">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  /* ------ RESULTS STATE ------ */
  return (
    <div>
      <div className="flow-step-nav">
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot active" />
        <span className="flow-step-label">Results</span>
      </div>

      {/* Verdict */}
      <div className="verdict-banner verdict-clean">
        <div className="verdict-icon">✅</div>
        <div style={{ flex: 1 }}>
          <div className="verdict-title">
            No Significant Technical Anomalies Detected
          </div>
          <div className="verdict-desc">
            Analysis of 16 sampled frames found no high-confidence manipulation
            artifacts. Minor compression artifacts are consistent with
            social-media re-encoding.
          </div>
          <div className="verdict-limitations">
            <div className="verdict-limitations-title">
              ⚠️ What this does NOT prove
            </div>
            <ul>
              <li>— This video has not been independently verified as authentic</li>
              <li>— Only 16 of ~1440 frames were sampled (85% coverage by scene)</li>
              <li>— Audio deepfake analysis was not performed</li>
              <li>— Absence of C2PA credentials is informational, not suspicious</li>
              <li>— This analysis is not a legal certificate of authenticity</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Results grid */}
      <div className="results-grid">
        {/* Keyframes */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🎞️ Sampled Keyframes</div>
            <span className="result-card-status status-clean">16 frames</span>
          </div>
          <div className="keyframes-grid">
            {MOCK_KEYFRAMES.map((kf, i) => (
              <div className="keyframe" key={i}>
                <div
                  className="keyframe-indicator"
                  style={{
                    background: kf.status === "clean" ? "#00d68f" : "#ffaa00",
                  }}
                />
                <div className="keyframe-time">{kf.time}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Detector */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🔬 Visual Detector</div>
            <span className="result-card-status status-clean">Low Risk</span>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="caption">Manipulation Score</span>
              <span style={{ color: "#00d68f", fontWeight: 700, fontSize: 14 }}>0.12</span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: "12%", background: "#00d68f" }} />
            </div>
          </div>
          <div className="caption">
            Model: SBI Detector v2.1 · CPU inference · 16 frames analyzed
          </div>
          <div className="tag tag-dark" style={{ marginTop: 12 }}>
            Threshold: 0.65 for &quot;Likely Manipulated&quot;
          </div>
        </div>

        {/* Metadata */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">📋 Technical Metadata</div>
            <span className="result-card-status status-info">Extracted</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px" }}>
            {[
              ["Container", "MP4 (isom)"],
              ["Codec", "H.264 High"],
              ["Resolution", "1080×1920"],
              ["Duration", "48s"],
              ["Frame Rate", "30 fps"],
              ["Audio", "AAC 44.1kHz"],
              ["File Size", "12.4 MB"],
              ["Created", "2026-08-18"],
            ].map(([k, v]) => (
              <div key={k} style={{ padding: "6px 0", borderBottom: "1px solid #2a2a2a" }}>
                <div className="caption" style={{ marginBottom: 2 }}>{k}</div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Provenance */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🔗 Provenance</div>
            <span className="result-card-status status-na">No Credentials</span>
          </div>
          <p style={{ fontSize: 14, color: "#b0b0b0", lineHeight: 1.7 }}>
            No C2PA content credentials were found in this file. This is{" "}
            <strong style={{ color: "#fff" }}>informational only</strong> — the
            absence of provenance data is not evidence of manipulation.
          </p>
          <div
            style={{
              marginTop: 16,
              padding: "12px 16px",
              background: "rgba(255,255,255,0.04)",
              borderRadius: 10,
              fontSize: 13,
              color: "#8a8a8a",
            }}
          >
            Most consumer devices and social platforms do not yet embed C2PA
            credentials. This status is expected for the majority of media.
          </div>
        </div>
      </div>

      {/* Evidence timeline */}
      <div className="result-card" style={{ marginTop: 24 }}>
        <div className="result-card-header">
          <div className="result-card-title">📊 Evidence Timeline</div>
        </div>
        <div className="evidence-timeline">
          {MOCK_EVIDENCE.map((ev, i) => (
            <div className="evidence-item" key={i}>
              <div className="evidence-dot" style={{ background: ev.color }} />
              <div className="evidence-content">
                <div className="evidence-title">{ev.title}</div>
                <div className="evidence-desc">{ev.desc}</div>
                <div className="evidence-meta">
                  {ev.meta.map((m, j) => (
                    <span key={j}>{m}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: 32, display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button className="btn-primary">
          Download Report <span className="btn-arrow" style={{ background: "white", color: "var(--dark)" }}>↓</span>
        </button>
        <button className="btn-secondary">Download JSON</button>
        <button className="btn-secondary" onClick={reset}>
          New Audit
        </button>
      </div>
    </div>
  );
}
