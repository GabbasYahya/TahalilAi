"""Quick E2E test: upload an image, poll for analysis result."""
import time
import httpx

IMAGE = r"C:\Users\pc\Desktop\tahalilAi\backend\uploads\c0cdf2bc-171f-463a-a87f-21b69b8a0399.png"

with open(IMAGE, "rb") as f:
    r = httpx.post(
        "http://127.0.0.1:8000/analyze",
        files={"file": ("test.png", f, "image/png")},
        data={"wait_for_result": "false"},
        timeout=30,
    )
    print("Submit:", r.json())
    job_id = r.json()["job_id"]

for i in range(120):
    time.sleep(5)
    s = httpx.get(f"http://127.0.0.1:8000/status/{job_id}", timeout=10)
    data = s.json()
    status = data.get("status")
    msg = data.get("message", "")
    print(f"  [{i*5}s] status={status}, msg={msg}")
    if status in ("completed", "failed"):
        if status == "completed":
            result = data["result"]
            analysis = result["analysis"]
            print(f"\n=== ANALYSIS ({len(analysis)} chars) ===")
            print(analysis[:2000])
            # Verify no prompt leak
            has_leak = any(x in analysis for x in [
                "[SYSTEM_PROMPT]", "[INST]", "Medical Results Explainer",
                "ONLY output English", "Do NOT output",
            ])
            print(f"\n--- PROMPT LEAK CHECK: {'FAIL' if has_leak else 'PASS'} ---")
            if "pdf_url" in result:
                print(f"PDF: {result['pdf_url']}")
        else:
            print(f"FAILED: {data.get('error')}")
        break
        break
