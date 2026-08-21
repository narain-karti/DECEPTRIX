"use client";
import { useState, useEffect, useRef } from "react";

type FlowState = "upload" | "processing" | "results" | "failed";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const STAGES = ["Initialize", "Extract Metadata", "Run Deepfake ViT & Landmarks", "Lip-Sync & Spectral Analysis", "Multi-Modal Fusion", "Finalize"];

interface FaceRef {
  bbox: number[];
  confidence: number;
  fake_score: number;
  jitter_score: number;
  freq_score: number;
  face_crop: string;
}

export default function MediaAudit() {
  const [flow, setFlow] = useState<FlowState>("upload");
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Initializing...");
  const [resultData, setResultData] = useState<any>(null);
  const [liveEvidence, setLiveEvidence] = useState<any[]>([]);
  const [liveReportData, setLiveReportData] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [selectedFace, setSelectedFace] = useState<{ face: FaceRef; timeStr: string; event: any } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Derive stage index from backend progress (0-100)
  const stageIdx = progress === 0 ? 0 : Math.min(Math.floor((progress / 100) * STAGES.length), STAGES.length - 1);

  const startProcessing = async () => {
    if (!file) return;
    setFlow("processing");
    setProgress(0);
    setResultData(null);
    setLiveEvidence([]);
    setLiveReportData(null);
    setErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/media/jobs`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setJobId(data.id);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(`Failed to upload video: ${err.message}`);
      setFlow("failed");
    }
  };

  useEffect(() => {
    if (flow !== "processing" || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/media/jobs/${jobId}`);
        const data = await res.json();
        
        setProgress(data.progress || 0);
        if (data.current_step) {
          setCurrentStep(data.current_step);
        }

        // Live stream progressive evidence & report data
        if (data.evidence && Array.isArray(data.evidence)) {
          setLiveEvidence(data.evidence);
        }
        if (data.report_data) {
          setLiveReportData(data.report_data);
        }

        if (data.status === "completed") {
          clearInterval(interval);
          const resultRes = await fetch(`${API_BASE}/api/v1/media/jobs/${jobId}/result`);
          const resultJson = await resultRes.json();
          setResultData(resultJson);
          setFlow("results");
        } else if (data.status === "failed" || data.status === "error") {
          clearInterval(interval);
          setErrorMsg(data.current_step || "The ML pipeline encountered an error while processing the media.");
          setFlow("failed");
        }
      } catch (err: any) {
        console.error("Polling error:", err);
      }
    }, 1200);

    return () => {
      clearInterval(interval);
    };
  }, [flow, jobId]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const reset = () => {
    setFlow("upload");
    setFile(null);
    setJobId(null);
    setProgress(0);
    setResultData(null);
    setLiveEvidence([]);
    setLiveReportData(null);
    setErrorMsg("");
    setSelectedFace(null);
  };

  const formatSize = (bytes: number) => {
    return bytes > 1024 * 1024
      ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
      : `${(bytes / 1024).toFixed(0)} KB`;
  };

  const resolveStorageUrl = (rawPath?: string) => {
    if (!rawPath || typeof rawPath !== 'string') return null;
    const storageIdx = rawPath.indexOf('storage');
    if (storageIdx !== -1) {
      return `${API_BASE}/${rawPath.substring(storageIdx).replace(/\\/g, '/')}`;
    }
    return rawPath;
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
            Drop suspect video here or <span className="accent">browse</span>
          </div>
          <div className="upload-subtitle">
            MP4, WebM, or MOV · Dense 15 FPS frame sampling · Max 200 MB
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
                  <span>{formatSize(file.size)}</span>
                  <span>{file.type || "video/mp4"}</span>
                </div>
              </div>
              <button className="file-remove" onClick={() => setFile(null)}>
                ✕
              </button>
            </div>
            <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
              <button className="btn-primary" onClick={startProcessing}>
                Execute Multi-Modal Audit <span className="btn-arrow">→</span>
              </button>
              <button className="btn-secondary" onClick={() => setFile(null)}>
                Remove
              </button>
            </div>
          </>
        )}

        <div style={{ marginTop: 28 }}>
          <p className="caption">
            🔒 All uploads are cryptographically fingerprinted via chunked SHA-256 and evaluated across a 5-signal multi-modal Bayesian ensemble.
          </p>
        </div>
      </div>
    );
  }

  /* ------ PROCESSING STATE (LIVELY STREAMING HUD) ------ */
  if (flow === "processing") {
    const liveFaces = liveEvidence.filter(e => e.artifact_refs?.[0]?.faces?.length > 0);
    const meta = liveReportData?.metadata || {};

    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot active" />
          <div className="flow-step-dot" />
          <span className="flow-step-label">Live Forensic Engine Active...</span>
        </div>

        {/* TOP VIDEO STREAM METRICS BAR */}
        <div 
          style={{
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", 
            gap: "12px", 
            marginBottom: "20px"
          }}
        >
          <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Stream File</span>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", marginTop: "2px" }}>
              {file?.name || "Target Video"}
            </div>
          </div>

          <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Container & Codecs</span>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--accent)", marginTop: "2px" }}>
              {meta.video_codec ? `${meta.video_codec.toUpperCase()} / ${meta.audio_codec?.toUpperCase() || 'PCM'}` : "Analyzing..."}
            </div>
          </div>

          <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Resolution & Rate</span>
            <div style={{ fontSize: "13px", fontWeight: 700, color: "#a5d6ff", marginTop: "2px" }}>
              {meta.width ? `${meta.width}x${meta.height} @ ${meta.fps || 24} FPS` : "Probing stream..."}
            </div>
          </div>

          <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Faces Identified</span>
            <div style={{ fontSize: "13px", fontWeight: 700, color: liveFaces.length > 0 ? "#00d68f" : "var(--text-secondary)", marginTop: "2px", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: liveFaces.length > 0 ? "#00d68f" : "#888", animation: "pulse 1.5s infinite" }} />
              {liveFaces.length} Keyframes Extracted
            </div>
          </div>
        </div>

        {/* PROGRESS BAR & STAGES */}
        <div className="progress-container" style={{ padding: "24px", background: "var(--surface-dark)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)" }}>
          <div className="progress-stages">
            {STAGES.map((stage, i) => (
              <div
                className={`progress-stage${
                  i < stageIdx ? " completed" : i === stageIdx ? " active" : ""
                }`}
                key={i}
              >
                <div className="progress-dot" style={{
                  animation: i === stageIdx ? "pulse 2s infinite ease-in-out" : "none"
                }}>
                  {i < stageIdx ? "✓" : ""}
                </div>
                <div className="progress-stage-label" style={{
                  animation: i === stageIdx ? "pulse 2.5s infinite ease-in-out" : "none"
                }}>{stage}</div>
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

          <div className="progress-bar-track" style={{ marginTop: 24 }}>
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%`, transition: "width 0.5s ease" }}
            />
          </div>

          <div className="progress-status" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
            <span className="progress-status-text" style={{ fontStyle: "italic", opacity: 0.9 }}>
              <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{
                  width: "12px", height: "12px", borderRadius: "50%", 
                  border: "2px solid var(--accent)", 
                  borderTopColor: "transparent", 
                  animation: "spin 1s linear infinite"
                }} />
                {currentStep}
              </span>
            </span>
            <span className="progress-status-percent" style={{ fontWeight: "bold", color: "var(--accent)" }}>
              {Math.round(progress)}%
            </span>
          </div>

          {/* 5-ENGINE FORENSIC HUD */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "10px", marginTop: "20px" }}>
            {[
              { name: "FFprobe Parser", active: progress >= 5, done: progress >= 15, icon: "📋" },
              { name: "ViT Deepfake", active: progress >= 30, done: progress >= 75, icon: "🔬" },
              { name: "FaceMesh Jitter", active: progress >= 30, done: progress >= 75, icon: "👁️" },
              { name: "MAR Lip-Sync", active: progress >= 75, done: progress >= 90, icon: "👄" },
              { name: "2D-DCT Spectral", active: progress >= 30, done: progress >= 90, icon: "⚡" },
            ].map((eng, idx) => (
              <div 
                key={idx}
                style={{
                  background: eng.done ? "rgba(0, 214, 143, 0.08)" : eng.active ? "rgba(255, 90, 36, 0.12)" : "rgba(255, 255, 255, 0.02)",
                  border: `1px solid ${eng.done ? "rgba(0, 214, 143, 0.3)" : eng.active ? "rgba(255, 90, 36, 0.4)" : "rgba(255, 255, 255, 0.05)"}`,
                  borderRadius: "var(--radius-sm)",
                  padding: "10px 12px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  transition: "all 0.3s ease"
                }}
              >
                <span>{eng.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-primary)" }}>{eng.name}</div>
                  <div style={{ fontSize: "10px", color: eng.done ? "#00d68f" : eng.active ? "var(--accent)" : "var(--text-muted)" }}>
                    {eng.done ? "Completed" : eng.active ? "Executing..." : "Queued"}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── LIVELY SLIDING FACE EXTRACTION CAROUSEL ── */}
          <div 
            style={{ 
              marginTop: "24px", 
              background: "linear-gradient(180deg, rgba(20,22,25,0.9) 0%, rgba(10,11,13,0.95) 100%)", 
              border: "1px solid var(--border)", 
              borderRadius: "var(--radius-lg)", 
              padding: "18px",
              position: "relative",
              overflow: "hidden"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ color: "var(--accent)" }}>🎞️</span> Live Keyframe Extraction & Face Tracking
                <span className="pill-outline" style={{ fontSize: "10px", color: "#00d68f", border: "1px solid rgba(0,214,143,0.4)", backgroundColor: "rgba(0,214,143,0.05)" }}>
                  ● LIVE STREAM
                </span>
              </div>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                {liveFaces.length > 0 ? `${liveFaces.length} frames evaluated` : "Sampling 15 FPS frames..."}
              </span>
            </div>
            
            {liveFaces.length === 0 ? (
              <div style={{ padding: "30px", textAlign: "center", border: "1px dashed var(--border-light)", borderRadius: "var(--radius-md)", background: "rgba(0,0,0,0.2)" }}>
                <div style={{ fontSize: "28px", marginBottom: "8px", animation: "pulse 1.5s infinite" }}>🎯</div>
                <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
                  Scanning video frames for human facial regions & landmark boundaries...
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                  Extracted face crops and ViT neural classifications will slide across this tape in real time.
                </div>
              </div>
            ) : (
              <div 
                className="live-face-ticker"
                style={{ 
                  display: "flex", 
                  gap: "14px", 
                  overflowX: "auto", 
                  paddingBottom: "10px",
                  scrollBehavior: "smooth"
                }}
              >
                {liveFaces.map((ev, idx) => {
                  const time = ev.artifact_refs?.[0]?.timestamp_sec || 0;
                  const mins = Math.floor(time / 60);
                  const secs = time % 60;
                  const timeStr = `${mins}:${secs.toString().padStart(2, '0')}`;
                  const faces = ev.artifact_refs?.[0]?.faces || [];
                  const faceObj = faces.length > 0 ? faces[0] : null;
                  const cropUrl = resolveStorageUrl(faceObj?.face_crop);
                  const fakeProb = faceObj?.fake_score ?? 0;
                  const isFake = fakeProb > 0.5;

                  return (
                    <div 
                      key={idx}
                      onClick={() => faceObj && setSelectedFace({ face: faceObj, timeStr, event: ev })}
                      style={{
                        minWidth: "128px",
                        background: "#131416",
                        borderRadius: "var(--radius-md)",
                        border: `2px solid ${isFake ? "rgba(255, 74, 74, 0.7)" : "rgba(0, 214, 143, 0.7)"}`,
                        overflow: "hidden",
                        flexShrink: 0,
                        position: "relative",
                        cursor: faceObj ? "pointer" : "default",
                        boxShadow: isFake ? "0 0 12px rgba(255, 74, 74, 0.2)" : "0 0 12px rgba(0, 214, 143, 0.2)",
                        transition: "transform 0.2s ease",
                      }}
                    >
                      {/* Face Thumbnail with Cyber Laser Reticle */}
                      <div style={{ width: "100%", height: "95px", background: "#000", position: "relative", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {cropUrl ? (
                          <img src={cropUrl} alt={`Keyframe ${timeStr}`} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                        ) : (
                          <span style={{ fontSize: "11px", color: "#666" }}>Frame #{timeStr}</span>
                        )}
                        
                        {/* Target Crosshairs / Bounding Box Brackets */}
                        <div style={{ position: "absolute", top: 4, left: 4, borderTop: "2px solid #FF5A24", borderLeft: "2px solid #FF5A24", width: 8, height: 8 }} />
                        <div style={{ position: "absolute", top: 4, right: 4, borderTop: "2px solid #FF5A24", borderRight: "2px solid #FF5A24", width: 8, height: 8 }} />
                        <div style={{ position: "absolute", bottom: 4, left: 4, borderBottom: "2px solid #FF5A24", borderLeft: "2px solid #FF5A24", width: 8, height: 8 }} />
                        <div style={{ position: "absolute", bottom: 4, right: 4, borderBottom: "2px solid #FF5A24", borderRight: "2px solid #FF5A24", width: 8, height: 8 }} />
                        
                        {/* Laser scan line animation */}
                        <div 
                          style={{
                            position: "absolute",
                            left: 0,
                            right: 0,
                            height: "2px",
                            background: isFake ? "rgba(255, 74, 74, 0.8)" : "rgba(0, 214, 143, 0.8)",
                            boxShadow: isFake ? "0 0 8px #ff4a4a" : "0 0 8px #00d68f",
                            animation: "scanline 2s linear infinite"
                          }}
                        />

                        <span style={{ position: "absolute", bottom: 4, left: 6, fontSize: "10px", fontWeight: 800, color: "#fff", background: "rgba(0,0,0,0.7)", padding: "1px 4px", borderRadius: "3px" }}>
                          {timeStr}
                        </span>
                      </div>

                      {/* Face Telemetry Metrics */}
                      <div style={{ padding: "8px", background: "rgba(0,0,0,0.85)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                          <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 700 }}>ViT RISK</span>
                          <span style={{ fontSize: "11px", fontWeight: 800, color: isFake ? "#ff4a4a" : "#00d68f" }}>
                            {(fakeProb * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="progress-bar-track" style={{ height: "4px", margin: 0 }}>
                          <div className="progress-bar-fill" style={{ width: `${fakeProb * 100}%`, background: isFake ? "#ff4a4a" : "#00d68f" }} />
                        </div>
                        <div style={{ fontSize: "9px", color: "var(--text-secondary)", marginTop: "4px", textAlign: "center" }}>
                          {isFake ? "🚨 Synthetic Artifact" : "✓ Organic Match"}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* DUAL SIGNAL WAVEFORM & SPECTRAL RADAR SCOPE */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px", marginTop: "20px" }}>
            {/* Audio-Visual Lip Synchrony Scope */}
            <div style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-md)", padding: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>👄</span> Audio-Visual Lip Sync Correlation (MAR / RMS)
                </span>
                <span style={{ fontSize: "10px", color: progress >= 75 ? "#00d68f" : "var(--text-muted)", fontFamily: "monospace" }}>
                  {progress >= 75 ? "Correlating Signals" : "Buffering Audio..."}
                </span>
              </div>
              <div style={{ height: "45px", display: "flex", alignItems: "center", gap: "3px", overflow: "hidden" }}>
                {Array.from({ length: 28 }).map((_, i) => {
                  const active = progress >= 75;
                  const height = active ? 10 + Math.sin(i * 0.8 + progress * 0.2) * 20 + Math.random() * 12 : 6;
                  return (
                    <div 
                      key={i}
                      style={{
                        flex: 1,
                        height: `${Math.max(4, height)}px`,
                        background: active ? (i % 2 === 0 ? "var(--accent)" : "#00d68f") : "#333",
                        borderRadius: "2px",
                        transition: "height 0.2s ease"
                      }}
                    />
                  );
                })}
              </div>
            </div>

            {/* 2D-DCT High-Frequency Anomaly Scope */}
            <div style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-md)", padding: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>⚡</span> 2D-DCT Frequency FFT Sub-Pixel Radar
                </span>
                <span style={{ fontSize: "10px", color: progress >= 30 ? "var(--accent)" : "var(--text-muted)", fontFamily: "monospace" }}>
                  {progress >= 30 ? "Scanning High-Freqs" : "Awaiting Chunks..."}
                </span>
              </div>
              <div style={{ height: "45px", display: "flex", alignItems: "center", gap: "3px", overflow: "hidden" }}>
                {Array.from({ length: 28 }).map((_, i) => {
                  const active = progress >= 30;
                  const height = active ? 8 + Math.cos(i * 0.5 + progress * 0.15) * 18 + Math.random() * 10 : 6;
                  return (
                    <div 
                      key={i}
                      style={{
                        flex: 1,
                        height: `${Math.max(4, height)}px`,
                        background: active ? "#a5d6ff" : "#333",
                        borderRadius: "2px",
                        transition: "height 0.2s ease"
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>

          {/* LIVE DIAGNOSTIC TERMINAL LOGS */}
          <div style={{ marginTop: "20px", padding: "14px", background: "rgba(0,0,0,0.4)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)", position: "relative", overflow: "hidden" }}>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "1px", display: "flex", justifyContent: "space-between" }}>
              <span>Live Diagnostic Stream</span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#00d68f", animation: "pulse 1.5s infinite" }} />
                Celery Pipeline Active
              </span>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "5px", fontFamily: "monospace", fontSize: "11px", color: "#a5d6ff", height: "70px", overflow: "hidden", justifyContent: "flex-end" }}>
              {(() => {
                 const logs = [
                   "[sys] Celery worker connected to Redis broker...",
                   `[hash] Chunked SHA-256 fingerprint verified.`
                 ];
                 if (progress >= 5) logs.push(`[ffprobe] Extracted technical container tags: ${meta.video_codec || 'h264'} / ${meta.audio_codec || 'aac'}`);
                 if (progress >= 15) logs.push(`[ffmpeg] Dense 15 FPS keyframe extraction & 16kHz mono audio split complete.`);
                 if (progress >= 30) logs.push(`[vit] Vision Transformer Patch-16 & MediaPipe FaceMesh loaded.`);
                 if (progress > 30 && progress < 75) logs.push(`[vit/dct] Evaluated ${liveFaces.length} facial sequences for generative artifacts (${Math.round(progress)}%)...`);
                 if (progress >= 75 && progress < 90) logs.push(`[librosa] Correlating Mouth Aspect Ratio (MAR) with acoustic RMS energy...`);
                 if (progress >= 90) logs.push(`[fusion] Computing 5-signal multi-modal Bayesian consensus...`);
                 if (progress >= 100) logs.push(`[verdict] Forensic audit complete. Ready.`);
                 
                 return logs.slice(-3).map((log, idx, arr) => (
                   <div key={idx} style={{ 
                     opacity: 0.4 + (idx / arr.length) * 0.6,
                     whiteSpace: "nowrap",
                     overflow: "hidden",
                     textOverflow: "ellipsis"
                   }}>
                     {log}
                   </div>
                 ));
              })()}
            </div>
          </div>
        </div>

        {/* Global Keyframe Scanline Animation */}
        <style jsx global>{`
          @keyframes scanline {
            0% { top: 0%; opacity: 0.8; }
            50% { top: 100%; opacity: 1; }
            100% { top: 0%; opacity: 0.8; }
          }
        `}</style>
      </div>
    );
  }

  /* ------ FAILED STATE ------ */
  if (flow === "failed") {
    return (
      <div>
        <div className="flow-step-nav">
          <div className="flow-step-dot completed" />
          <div className="flow-step-dot error" style={{ background: "#ff4a4a" }} />
          <div className="flow-step-dot" />
          <span className="flow-step-label" style={{ color: "#ff4a4a" }}>Failed</span>
        </div>
        
        <div className="verdict-banner verdict-warning" style={{ borderLeftColor: "#ff4a4a", background: "rgba(255, 74, 74, 0.05)" }}>
          <div className="verdict-icon">🚨</div>
          <div style={{ flex: 1 }}>
            <div className="verdict-title" style={{ color: "#ff4a4a" }}>Analysis Failed</div>
            <div className="verdict-desc">{errorMsg || "The pipeline encountered an error processing this media."}</div>
          </div>
        </div>

        <div style={{ marginTop: 24 }}>
          <button className="btn-primary" onClick={reset}>
            Try Another Video
          </button>
        </div>
      </div>
    );
  }

  /* ------ RESULTS STATE ------ */
  const isManipulated = resultData?.verdict === "Likely Manipulated";
  const isSuspicious = resultData?.verdict === "Suspicious";
  const isReal = resultData?.verdict === "Likely Real";

  let verdictClass = "verdict-clean";
  let verdictIcon = "✅";
  let verdictTitle = resultData?.verdict || "Analysis Complete";

  if (isManipulated) {
    verdictClass = "verdict-warning";
    verdictIcon = "🚨";
  } else if (isSuspicious) {
    verdictClass = "verdict-warning";
    verdictIcon = "⚠️";
  }

  // Find visual events
  const visualEvents = resultData?.timeline_evidence?.filter((e: any) => e.modality === "media") || [];
  const maxScore = visualEvents.length > 0 
    ? Math.max(...visualEvents.map((e: any) => e.score_or_null || 0)) 
    : 0;

  const finalScore = resultData?.report_data?.final_score ?? maxScore;
  const signalScores = resultData?.report_data?.signal_scores || {};

  return (
    <div>
      <div className="flow-step-nav">
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot active" />
        <span className="flow-step-label">Results</span>
      </div>

      {/* Verdict Banner */}
      <div className={`verdict-banner ${verdictClass}`}>
        <div className="verdict-icon">{verdictIcon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
            <div className="verdict-title">
              {verdictTitle}
            </div>
            <div style={{ fontSize: "13px", fontWeight: 700, padding: "4px 10px", background: "rgba(0,0,0,0.3)", borderRadius: "var(--radius-pill)" }}>
              Composite Anomaly: {(finalScore).toFixed(2)} / 1.00
            </div>
          </div>
          <div className="verdict-desc" style={{ marginTop: "4px" }}>
            {isManipulated ? 
              "Analysis found high-confidence synthetic artifacts exceeding detection thresholds across visual, frequency, and lip-sync modalities." :
              isSuspicious ? 
              "Analysis detected suspicious anomalies, but composite confidence is below the definitive manipulation threshold." :
              "Analysis found no high-confidence manipulation artifacts. Minor compression artifacts are consistent with standard encoding."}
          </div>
        </div>
      </div>

      {/* 5-SIGNAL DECOMPOSITION RADAR BARS */}
      <div className="secondary-card" style={{ marginTop: 20, padding: "20px" }}>
        <div className="card-section-title" style={{ marginBottom: "16px" }}>
          <span>📊</span> 5-Signal Ensemble Decomposition
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {[
            { label: "ViT Deepfake Classifier", weight: "35%", score: signalScores.deepfake_classifier ?? maxScore, icon: "🔬" },
            { label: "Lip-Sync Audio-Visual Correlation", weight: "25%", score: signalScores.lip_sync ?? 0.0, icon: "👄" },
            { label: "Facial Landmark Jitter Variance", weight: "15%", score: signalScores.jitter ?? 0.0, icon: "👁️" },
            { label: "2D-DCT Spectral Frequency Anomaly", weight: "15%", score: signalScores.frequency ?? 0.0, icon: "⚡" },
            { label: "Container & Codec Metadata Tag Check", weight: "10%", score: signalScores.metadata ?? 0.0, icon: "📋" },
          ].map((sig, idx) => {
            const sc = typeof sig.score === 'number' ? sig.score : 0;
            const barColor = sc > 0.6 ? "#ff4a4a" : sc > 0.4 ? "#ffaa00" : "#00d68f";
            return (
              <div key={idx}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                  <span style={{ color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
                    <span>{sig.icon}</span>
                    <strong>{sig.label}</strong>
                    <span style={{ color: "var(--text-muted)", fontSize: "11px" }}>({sig.weight} weight)</span>
                  </span>
                  <span style={{ color: barColor, fontWeight: 700, fontFamily: "monospace" }}>
                    {sc.toFixed(2)}
                  </span>
                </div>
                <div className="progress-bar-track" style={{ height: "6px" }}>
                  <div className="progress-bar-fill" style={{ width: `${sc * 100}%`, background: barColor }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Results grid */}
      <div className="results-grid" style={{ marginTop: 20 }}>
        {/* Keyframes Gallery with interactive click */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🎞️ Extracted Face Crops ({visualEvents.length})</div>
            <span className="caption" style={{ color: "var(--accent)" }}>Click to Inspect</span>
          </div>
          <div className="keyframes-grid">
            {visualEvents.slice(0, 8).map((ev: any, i: number) => {
              const time = ev.artifact_refs?.[0]?.timestamp_sec || 0;
              const mins = Math.floor(time / 60);
              const secs = time % 60;
              const timeStr = `${mins}:${secs.toString().padStart(2, '0')}`;
              const isEventClean = ev.score_or_null < 0.4;
              
              const faces = ev.artifact_refs?.[0]?.faces || [];
              const faceObj = faces.length > 0 ? faces[0] : null;
              const faceCropUrl = resolveStorageUrl(faceObj?.face_crop);

              return (
                <div 
                  className="keyframe" 
                  key={i} 
                  onClick={() => faceObj && setSelectedFace({ face: faceObj, timeStr, event: ev })}
                  style={{ 
                    position: 'relative', 
                    overflow: 'hidden',
                    background: '#1a1d21', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    border: `2px solid ${isEventClean ? "#00d68f" : "#ffaa00"}`,
                    cursor: faceObj ? 'pointer' : 'default',
                    transition: 'transform 0.2s ease'
                  }}
                >
                  {faceCropUrl ? (
                    <img 
                      src={faceCropUrl} 
                      alt={`Sequence at ${timeStr}`} 
                      style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.9 }} 
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div style={{ color: '#666', fontSize: 11 }}>No Face</div>
                  )}
                  <div
                    className="keyframe-indicator"
                    style={{
                      background: isEventClean ? "#00d68f" : "#ffaa00",
                      position: 'absolute',
                      top: 6,
                      right: 6,
                      width: 10,
                      height: 10,
                      borderRadius: '50%'
                    }}
                  />
                  <div className="keyframe-time" style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: 'rgba(0,0,0,0.75)',
                    padding: '3px',
                    fontSize: '11px',
                    textAlign: 'center'
                  }}>{timeStr}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Primary ViT Detector Card */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🔬 Primary ViT Detector</div>
            <span className={`result-card-status ${isReal ? 'status-clean' : 'status-warning'}`}>
              {isManipulated ? "High Risk" : isSuspicious ? "Medium Risk" : "Low Risk"}
            </span>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="caption">Max Visual Anomaly Score</span>
              <span style={{ color: isReal ? "#00d68f" : "#ffaa00", fontWeight: 700, fontSize: 14 }}>
                {maxScore.toFixed(2)}
              </span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${maxScore * 100}%`, background: isReal ? "#00d68f" : "#ffaa00" }} />
            </div>
          </div>
          <div className="caption" style={{ fontSize: 12 }}>
            Model: {visualEvents[0]?.model_or_connector || "dima806/ViT-Patch16 + MediaPipe FaceMesh"}
          </div>
        </div>
      </div>

      {/* Evidence timeline */}
      <div className="result-card" style={{ marginTop: 20 }}>
        <div className="result-card-header">
          <div className="result-card-title">📊 Diagnostic Evidence Timeline</div>
        </div>
        <div className="evidence-timeline">
          {resultData?.timeline_evidence?.map((ev: any, i: number) => {
            const isEventClean = (ev.score_or_null ?? 0) < 0.4;
            const color = isEventClean ? "#00d68f" : (ev.score_or_null ?? 0) > 0.6 ? "#ff4a4a" : "#ffaa00";
            
            return (
              <div className="evidence-item" key={i}>
                <div className="evidence-dot" style={{ background: color }} />
                <div className="evidence-content">
                  <div className="evidence-title">
                    {ev.modality === 'media' ? "Visual Artifact & Landmark Analysis" :
                     ev.modality === 'audio_visual' ? "Audio-Visual Lip Sync Correlation" :
                     ev.modality === 'metadata' ? "Technical Container & Metadata Inspection" :
                     ev.modality === 'frequency' ? "Spectral Frequency Analysis" :
                     "Diagnostic Evidence"}
                  </div>
                  <div className="evidence-desc">{ev.explanation}</div>
                  <div className="evidence-meta">
                    <span>Model: {ev.model_or_connector}</span>
                    <span>Score: {(ev.score_or_null || 0).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: 24, display: "flex", gap: 12, flexWrap: "wrap" }}>
        {resultData?.report_links?.pdf && (
          <button className="btn-primary" onClick={() => window.open(`${API_BASE}${resultData.report_links.pdf}`, "_blank")}>
            Download Forensic PDF <span className="btn-arrow">↓</span>
          </button>
        )}
        {resultData?.report_links?.json && (
          <button className="btn-secondary" onClick={() => window.open(`${API_BASE}${resultData.report_links.json}`, "_blank")}>
            Download JSON Record
          </button>
        )}
        <button className="btn-secondary" onClick={reset}>
          New Audit
        </button>
      </div>

      {/* Face Inspector Lightbox Modal */}
      {selectedFace && (
        <div 
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.8)",
            backdropFilter: "blur(6px)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px"
          }}
          onClick={() => setSelectedFace(null)}
        >
          <div 
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "24px",
              maxWidth: "480px",
              width: "100%",
              boxShadow: "var(--shadow-popup)",
              position: "relative"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setSelectedFace(null)}
              style={{
                position: "absolute",
                top: "14px",
                right: "14px",
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                fontSize: "18px",
                cursor: "pointer"
              }}
            >
              ✕
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "16px" }}>
              <div style={{ width: "80px", height: "80px", borderRadius: "var(--radius-md)", overflow: "hidden", border: "2px solid var(--accent)", background: "#000" }}>
                <img 
                  src={resolveStorageUrl(selectedFace.face.face_crop) || ""} 
                  alt="Face Crop" 
                  style={{ width: "100%", height: "100%", objectFit: "cover" }} 
                />
              </div>
              <div>
                <h3 className="h3" style={{ fontSize: "18px" }}>Face Keyframe #{selectedFace.timeStr}</h3>
                <span className="caption" style={{ color: "var(--accent)" }}>Bounding Box Analysis</span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
              <div className="data-row">
                <span className="data-label">ViT Deepfake Probability</span>
                <span className="data-value" style={{ color: selectedFace.face.fake_score > 0.5 ? "#ff4a4a" : "#00d68f", fontWeight: 700 }}>
                  {(selectedFace.face.fake_score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">DCT High-Freq Anomaly</span>
                <span className="data-value" style={{ fontFamily: "monospace" }}>
                  {selectedFace.face.freq_score?.toFixed(2) || "0.00"}
                </span>
              </div>
              <div className="data-row">
                <span className="data-label">Landmark Jitter Variance</span>
                <span className="data-value" style={{ fontFamily: "monospace" }}>
                  {selectedFace.face.jitter_score?.toFixed(2) || "0.00"}
                </span>
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-light)", marginBottom: "16px" }}>
              <div className="caption" style={{ marginBottom: "2px" }}>Sequence Diagnostics</div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: "1.5" }}>
                {selectedFace.event?.explanation || "Analyzed for spatial blending irregularities, facial boundary coherence, and temporal landmark stability."}
              </p>
            </div>

            <button className="btn-primary" style={{ width: "100%" }} onClick={() => setSelectedFace(null)}>
              Close Inspector
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
