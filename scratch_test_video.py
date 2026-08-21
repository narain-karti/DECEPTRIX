import time
import httpx
import json

API_URL = "http://127.0.0.1:8000"
VIDEO_PATH = r"c:\Users\pnara\OneDrive\Desktop\DECEPTRIX\WhatsApp Video 2026-08-20 at 5.26.11 PM.mp4"

def run_test():
    print(f"Uploading {VIDEO_PATH} to DECEPTRIX API...")
    with open(VIDEO_PATH, "rb") as f:
        files = {"file": ("whatsapp_video.mp4", f, "video/mp4")}
        res = httpx.post(f"{API_URL}/api/v1/media/jobs", files=files, timeout=60.0)
    
    if res.status_code != 200:
        print(f"Upload failed: {res.status_code} {res.text}")
        return
    
    job_data = res.json()
    job_id = job_data["id"]
    print(f"Job created successfully! ID: {job_id}")
    print(f"SHA-256: {job_data.get('sha256')}")
    
    print("\nPolling job progress...")
    start_time = time.time()
    while True:
        r = httpx.get(f"{API_URL}/api/v1/media/jobs/{job_id}", timeout=10.0)
        status_data = r.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        step = status_data.get("current_step", "")
        evidence_count = len(status_data.get("evidence", []))
        
        print(f"[{time.time()-start_time:.1f}s] Progress: {progress}% | Status: {status} | Step: {step} | Evidences: {evidence_count}")
        
        if status == "completed":
            break
        elif status in ("failed", "error"):
            print(f"Job failed! Step: {step}")
            return
        
        time.sleep(2)
        
    print("\nFetching full forensic result...")
    result_res = httpx.get(f"{API_URL}/api/v1/media/jobs/{job_id}/result", timeout=10.0)
    result = result_res.json()
    
    print("=" * 60)
    print("FINAL FORENSIC VERDICT:", result.get("verdict"))
    print("=" * 60)
    print("\nTIMELINE EVIDENCE EVENTS:")
    for ev in result.get("timeline_evidence", []):
        print(f"\n- Modality: {ev.get('modality')}")
        print(f"  Type: {ev.get('type')}")
        print(f"  Model: {ev.get('model_or_connector')}")
        print(f"  Score: {ev.get('score_or_null')}")
        print(f"  Severity: {ev.get('severity')}")
        print(f"  Explanation: {ev.get('explanation')}")
        if ev.get("artifact_refs"):
            faces = ev["artifact_refs"][0].get("faces", [])
            for face in faces:
                print(f"    * Face BBox: {face.get('bbox')}")
                print(f"    * ViT Deepfake Score: {face.get('fake_score'):.4f}")
                print(f"    * 2D-DCT Freq Anomaly: {face.get('freq_score'):.4f}")
                print(f"    * Jitter Variance: {face.get('jitter_score'):.4f}")
                print(f"    * Crop File: {face.get('face_crop')}")
                
    pdf_link = result.get("report_links", {}).get("pdf")
    json_link = result.get("report_links", {}).get("json")
    print(f"\nPDF Report URL: {API_URL}{pdf_link}")
    print(f"JSON Record URL: {API_URL}{json_link}")
    
    if pdf_link:
        pdf_res = httpx.get(f"{API_URL}{pdf_link}", timeout=30.0)
        out_pdf = f"scratch_{job_id}.pdf"
        with open(out_pdf, "wb") as f:
            f.write(pdf_res.content)
        print(f"Saved PDF locally as: {out_pdf} ({len(pdf_res.content)} bytes)")

if __name__ == "__main__":
    run_test()
