"use client";
import { useState, useEffect, useRef } from "react";

type FlowState = "upload" | "processing" | "results" | "failed";

const STAGES = ["Initialize", "Extract Sequences", "Run Spatio-Temporal Models", "Analyze Audio", "Fuse Results", "Finalize"];

export default function MediaAudit() {
  const [flow, setFlow] = useState<FlowState>("upload");
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Initializing...");
  const [resultData, setResultData] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Derive stage index from backend progress (0-100)
  const stageIdx = progress === 0 ? 0 : Math.min(Math.floor((progress / 100) * STAGES.length), STAGES.length - 1);

  const startProcessing = async () => {
    if (!file) return;
    setFlow("processing");
    setProgress(0);
    setResultData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/media/jobs", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setJobId(data.id);
    } catch (err: any) {
      console.error(err);
      alert(`Failed to upload video to backend API. Error: ${err.message}`);
      setFlow("upload");
    }
  };

  useEffect(() => {
    if (flow !== "processing" || !jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/media/jobs/${jobId}`);
        const data = await res.json();
        
        setProgress(data.progress);
        if (data.current_step) {
          setCurrentStep(data.current_step);
        }

        if (data.status === "completed") {
          clearInterval(interval);
          const resultRes = await fetch(`http://127.0.0.1:8000/api/v1/media/jobs/${jobId}/result`);
          const resultJson = await resultRes.json();
          setResultData(resultJson);
          setFlow("results");
        } else if (data.status === "failed" || data.status === "error") {
          clearInterval(interval);
          setErrorMsg("The ML pipeline encountered an error while processing the media. Please ensure the video is valid and try again.");
          setFlow("failed");
        }
      } catch (err: any) {
        console.error("Polling error:", err);
        // Optional: If we want to fail on network disconnect, we can do it here.
      }
    }, 2000);

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
  };

  const formatSize = (bytes: number) => {
    return bytes > 1024 * 1024
      ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
      : `${(bytes / 1024).toFixed(0)} KB`;
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
            ⚠️ By uploading, you accept that processing occurs on our servers.
            Files are deleted after analysis.
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
                <span>{formatSize(file.size)}</span>
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
              style={{ width: `${progress}%`, transition: "width 0.5s ease" }}
            />
          </div>
          <div className="progress-status" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="progress-status-text" style={{ fontStyle: "italic", opacity: 0.8 }}>
              {stageIdx < STAGES.length
                ? currentStep
                : "Finalizing..."}
            </span>
            <span className="progress-status-percent" style={{ fontWeight: "bold" }}>
              {Math.round(progress)}%
            </span>
          </div>
        </div>
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
            <div className="verdict-desc">{errorMsg}</div>
          </div>
        </div>

        <div style={{ marginTop: 32 }}>
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

  // Find max visual score
  const visualEvents = resultData?.timeline_evidence?.filter((e: any) => e.modality === "media") || [];
  const maxScore = visualEvents.length > 0 
    ? Math.max(...visualEvents.map((e: any) => e.score_or_null || 0)) 
    : 0;

  return (
    <div>
      <div className="flow-step-nav">
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot completed" />
        <div className="flow-step-dot active" />
        <span className="flow-step-label">Results</span>
      </div>

      {/* Verdict */}
      <div className={`verdict-banner ${verdictClass}`}>
        <div className="verdict-icon">{verdictIcon}</div>
        <div style={{ flex: 1 }}>
          <div className="verdict-title">
            {verdictTitle}
          </div>
          <div className="verdict-desc">
            {isManipulated ? 
              "Analysis found high-confidence spatio-temporal artifacts consistent with deepfake manipulation." :
              isSuspicious ? 
              "Analysis found suspicious artifacts, but they were below the high-confidence threshold." :
              "Analysis found no high-confidence manipulation artifacts. Minor compression artifacts are consistent with social-media re-encoding."}
          </div>
        </div>
      </div>

      {/* Results grid */}
      <div className="results-grid">
        {/* Keyframes */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🎞️ Sequence Analysis</div>
            <span className={`result-card-status ${isReal ? 'status-clean' : 'status-warning'}`}>
              {visualEvents.length} clips
            </span>
          </div>
          <div className="keyframes-grid">
            {visualEvents.slice(0, 6).map((ev: any, i: number) => {
              const time = ev.artifact_refs?.[0]?.timestamp_sec || 0;
              const mins = Math.floor(time / 60);
              const secs = time % 60;
              const timeStr = `${mins}:${secs.toString().padStart(2, '0')}`;
              const isEventClean = ev.score_or_null < 0.4;
              
              // Get the face crop image path if available
              const faces = ev.artifact_refs?.[0]?.faces || [];
              let faceCropPath = faces.length > 0 ? faces[0].face_crop : null;
              
              // We need to convert the local file path to a URL path through the storage mount
              // e.g. "apps/api/storage/..." -> "/storage/..."
              if (faceCropPath && typeof faceCropPath === 'string') {
                const storageIdx = faceCropPath.indexOf('storage');
                if (storageIdx !== -1) {
                   faceCropPath = `http://127.0.0.1:8000/${faceCropPath.substring(storageIdx).replace(/\\/g, '/')}`;
                }
              }

              return (
                <div className="keyframe" key={i} style={{ 
                  position: 'relative', 
                  overflow: 'hidden',
                  background: '#1a1d21', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  border: `2px solid ${isEventClean ? "#00d68f" : "#ffaa00"}`
                }}>
                  {faceCropPath ? (
                    <img 
                      src={faceCropPath} 
                      alt={`Sequence at ${timeStr}`} 
                      style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.8 }} 
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div style={{ color: '#666', fontSize: 12 }}>No Face</div>
                  )}
                  <div
                    className="keyframe-indicator"
                    style={{
                      background: isEventClean ? "#00d68f" : "#ffaa00",
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      width: 12,
                      height: 12,
                      borderRadius: '50%'
                    }}
                  />
                  <div className="keyframe-time" style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    background: 'rgba(0,0,0,0.7)',
                    padding: '4px',
                    textAlign: 'center'
                  }}>{timeStr}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detector */}
        <div className="result-card">
          <div className="result-card-header">
            <div className="result-card-title">🔬 Visual Detector</div>
            <span className={`result-card-status ${isReal ? 'status-clean' : 'status-warning'}`}>
              {isManipulated ? "High Risk" : isSuspicious ? "Medium Risk" : "Low Risk"}
            </span>
          </div>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span className="caption">Max Manipulation Score</span>
              <span style={{ color: isReal ? "#00d68f" : "#ffaa00", fontWeight: 700, fontSize: 14 }}>
                {maxScore.toFixed(2)}
              </span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${maxScore * 100}%`, background: isReal ? "#00d68f" : "#ffaa00" }} />
            </div>
          </div>
          <div className="caption">
            Model: 3D ConvNet VideoMAE · {visualEvents.length} sequences analyzed
          </div>
        </div>
      </div>

      {/* Evidence timeline */}
      <div className="result-card" style={{ marginTop: 24 }}>
        <div className="result-card-header">
          <div className="result-card-title">📊 Evidence Timeline</div>
        </div>
        <div className="evidence-timeline">
          {resultData?.timeline_evidence?.map((ev: any, i: number) => {
            const isEventClean = ev.score_or_null < 0.4;
            const color = isEventClean ? "#00d68f" : ev.score_or_null > 0.6 ? "#ff4a4a" : "#ffaa00";
            
            return (
              <div className="evidence-item" key={i}>
                <div className="evidence-dot" style={{ background: color }} />
                <div className="evidence-content">
                  <div className="evidence-title">
                    {ev.modality === 'media' ? "Spatio-Temporal Sequence Analysis" : "Audio Deepfake Analysis"}
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
      <div style={{ marginTop: 32, display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button className="btn-primary" onClick={() => window.open(`http://127.0.0.1:8000${resultData.report_links.pdf}`, "_blank")}>
          Download PDF Report <span className="btn-arrow">↓</span>
        </button>
        <button className="btn-secondary" onClick={() => window.open(`http://127.0.0.1:8000${resultData.report_links.json}`, "_blank")}>
          Download JSON
        </button>
        <button className="btn-secondary" onClick={reset}>
          New Audit
        </button>
      </div>
    </div>
  );
}
