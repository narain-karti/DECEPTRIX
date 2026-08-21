import httpx
import time

with open("WhatsApp Video 2026-08-20 at 5.26.11 PM.mp4", "rb") as f:
    t0 = time.time()
    r = httpx.post("http://127.0.0.1:8000/api/v1/media/jobs", files={"file": ("test.mp4", f, "video/mp4")})
    post_time = time.time() - t0

print(f"POST Endpoint Latency: {post_time:.3f}s (Should be < 0.2s for non-blocking)")
job_data = r.json()
print("Job Response:", job_data)
job_id = job_data["id"]

for i in range(25):
    time.sleep(0.5)
    poll = httpx.get(f"http://127.0.0.1:8000/api/v1/media/jobs/{job_id}").json()
    faces_count = sum(len(ref.get("faces", [])) for ev in (poll.get("evidence") or []) for ref in (ev.get("artifact_refs") or []))
    print(f"Poll #{i+1:02d} | Status: {poll.get('status')} | Progress: {poll.get('progress')}% | Step: {poll.get('current_step')} | Faces: {faces_count}")
    if poll.get("status") == "completed":
        print("Analysis completed successfully in real-time!")
        break
