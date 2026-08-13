import json, time
from pathlib import Path
import httpx

BASE="http://127.0.0.1:8000/api"
upload=json.loads(Path("test-upload.json").read_text(encoding="utf-8-sig"))
common={
    "direction":"儿童互动陪伴玩具，友好、可量产、有明确玩法升级",
    "instruction":"方案要具体，说明结构继承或特性迁移关系，并给出可执行的量产风险提示。",
    "count":1,
    "asset_id":upload["id"],
    "analysis":upload["analysis"],
}
jobs={}
with httpx.Client(timeout=30) as client:
    for mode in ("structure","feature","both"):
        response=client.post(f"{BASE}/projects/proj-001/generate",json={**common,"mode":mode})
        response.raise_for_status(); jobs[mode]=response.json()["id"]
    deadline=time.time()+240
    results={}
    while time.time()<deadline and len(results)<3:
        for mode,job_id in jobs.items():
            if mode in results: continue
            state=client.get(f"{BASE}/jobs/{job_id}").json()
            if state["status"] in ("completed","failed"): results[mode]=state
        time.sleep(2)
Path("test-modes-results.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
for mode in ("structure","feature","both"):
    state=results.get(mode,{})
    plan=(state.get("plans") or [{}])[0]
    print(mode,state.get("status"),state.get("progress"),plan.get("type"),bool(plan.get("image_url")),plan.get("image_error", ""))
