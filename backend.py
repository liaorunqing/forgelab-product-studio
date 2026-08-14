from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import asyncio, base64, json, os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(exist_ok=True)
ARK_BASE = "https://ark.cn-beijing.volces.com/api/v3"

app = FastAPI(title="ForgeLab Product OS", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/assets", StaticFiles(directory=ROOT), name="frontend-assets")
projects = [{"id":"proj-001","name":"星际探索系列","status":"方案生成","created_at":"2026-08-13T09:20:00Z","asset":"星际探索者_原型01.png"}]
jobs = {}
asset_paths = {}

class Brief(BaseModel):
    direction: str = "未来城市 · 夜间救援"
    instruction: str = "保留原型的圆润轮廓与四轮比例，强调可靠、友善、可量产。"
    count: int = Field(default=6, ge=1, le=6)
    asset_id: str | None = None
    mode: str = "both"
    analysis: dict | None = None

class DescriptionInput(BaseModel):
    description: str = Field(min_length=10)

class ApiConfigInput(BaseModel):
    api_key: str = Field(min_length=10, max_length=500)
    vision_model: str = Field(default="doubao-seed-1-6-vision", max_length=200)
    llm_model: str = Field(default="doubao-seed-2-0-lite-260215", max_length=200)
    image_model: str = Field(default="doubao-seedream-4-0-250828", max_length=200)
    image_size: str = Field(default="2K", max_length=20)

def api_key(): return os.getenv("ARK_API_KEY", "").strip()
def configured(): return bool(api_key())
def headers(): return {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"}

def save_env_config(data: ApiConfigInput):
    values = {
        "ARK_API_KEY": data.api_key.strip(),
        "ARK_VISION_MODEL": data.vision_model.strip(),
        "ARK_LLM_MODEL": data.llm_model.strip(),
        "ARK_IMAGE_MODEL": data.image_model.strip(),
        "ARK_IMAGE_SIZE": data.image_size.strip() or "2K",
    }
    ROOT.joinpath(".env").write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    os.environ.update(values)

def fallback_concepts():
    rows = [("月面信使 · Lunar Courier","同源改款","白色外壳升级为月尘银，加入橙色信号灯与夜间救援识别条。",96,3,"orange"),("深海探针 · Abyss Scout","衍生方案","深海蓝防水外壳与荧光黄色标记，探索未知海域的微型伙伴。",91,4,"blue"),("花园精灵 · Garden Bot","衍生方案","柔和薄荷绿与种子舱设计，让每一次探索都带回新的生命。",89,5,"pink"),("火星邮差 · Mars Relay","衍生方案","赤红隔热外壳与可见式天线，适合远距离自动投递任务。",88,4,"orange"),("极地守望 · Polar Scout","衍生方案","冰川白与电光蓝组合，强调低温环境中的安全陪伴。",87,3,"blue"),("森林采样员 · Grove Bot","衍生方案","苔藓绿软质包覆，加入可拆卸样本盒与环境提示灯。",85,5,"pink")]
    return [{"id":f"plan-{i+1:03}","name":a,"type":b,"appearance":c,"match":d,"changes":e,"color":f,"image_url":None,"status":"ready","source":"fallback"} for i,(a,b,c,d,e,f) in enumerate(rows)]

async def ark_chat(messages, model_env="ARK_LLM_MODEL"):
    defaults = {"ARK_VISION_MODEL":"doubao-seed-1-6-vision", "ARK_LLM_MODEL":"doubao-seed-2-0-lite-260215"}
    model = os.getenv(model_env, defaults.get(model_env, ""))
    if not api_key() or not model: return None
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{ARK_BASE}/chat/completions", headers=headers(), json={"model":model,"messages":messages,"temperature":0.7})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

ANALYSIS_PROMPT = '''你是消费玩具产品分析师。根据输入素材整理产品定义。严格输出 JSON，不要 Markdown：
{"appearance":"形态、尺寸比例、材质、颜色、交互界面","functions":"核心功能清单","play":"用户如何操作、反馈和循环玩法","principle":"实现功能的机械/电子/软件原理；不可见部分必须标注推测","mechanics":"可见结构、关节、传动、运动自由度和关键相对位置","electronics":"可见电子件；不可见内容写图片不可见/视频不可见，不得编造","selling_points":"核心卖点、目标用户、使用场景","reusable_traits":"可迁移到其他产品的核心特性","pain_points":"现有痛点、装配和量产风险"}。区分可见事实与合理推测。'''

def media_data(path: Path):
    mime={".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}.get(path.suffix.lower(),"image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"

def extract_video_frames(path: Path, count=5):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("缺少 opencv-python-headless，无法解析视频") from exc
    cap=cv2.VideoCapture(str(path)); total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); frames=[]
    if total <= 0: raise RuntimeError("无法读取视频")
    positions=[total//2] if count==1 else [int((total-1)*n/(count-1)) for n in range(count)]
    for i,pos in enumerate(positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES,pos); ok,frame=cap.read()
        if ok:
            out=UPLOADS/f"{path.stem}-frame-{i}.jpg"; cv2.imwrite(str(out),frame); frames.append(out)
    cap.release()
    if not frames: raise RuntimeError("未能提取视频关键帧")
    return frames

async def analyze_asset(path: Path):
    if not configured(): return {"appearance":"圆润的机器人探索车体，主体为哑光白色，顶部配有橙色透明观察舱。","mechanics":"四轮独立驱动结构","confidence":98.4,"source":"fallback"}
    paths=extract_video_frames(path) if path.suffix.lower() in {".mp4",".mov"} else [path]
    content=[{"type":"text","text":ANALYSIS_PROMPT}]+[{"type":"image_url","image_url":{"url":media_data(p)}} for p in paths]
    text = await ark_chat([{"role":"user","content":content}], "ARK_VISION_MODEL")
    try: return {**json.loads(text), "confidence":92.0, "source":"ark"}
    except Exception: return {"appearance":text,"mechanics":"图片不可见","confidence":80.0,"source":"ark"}

async def generate_with_llm(brief: Brief, analysis):
    if not configured(): return fallback_concepts()[:brief.count]
    system = '''你是玩具工厂的产品策划师兼结构工程师。你会输出两类方案：
A·同结构升级：核心是“换壳不换芯”。必须保持原型轮廓包络、头身比例、屏幕位置、四肢/轮组数量与轴心、关节和底盘尺寸；电路板、电机、传感器、屏幕、电池仓、传动机构全部复用；只改变外壳表面、装饰件、纹理与配色，可在不新增硬件的前提下升级玩法。image_prompt 必须要求保留参考图精确结构。
B·特性迁移：提取原产品的核心交互、反馈机制、情绪价值和目标用户需求，迁移为不同形态的新产品。此路线可以使用不同结构，但必须清楚说明哪些是迁移的特性，不能宣称复用原型硬件。
所有方案都必须说明用户玩法、卖点、实现边界、装配或量产风险。只输出 JSON 数组，每项字段 name,type,appearance,changes,gameplay,selling_points,risks,image_prompt。'''
    mode_rule={
        "structure":"只生成A路线：结构相似产品。严格复用原理、内部机构、部件相对位置和整体包络，可改变外壳并升级玩法。",
        "feature":"只生成B路线：特性迁移产品。提取 reusable_traits 和核心用户价值，迁移到不同产品形态，不宣称复用原硬件。",
        "both":"同时生成两条路线：至少1套A路线结构相似改款，其余为B路线特性迁移新品；每项 type 必须明确写“A·同结构升级”或“B·特性迁移”。"
    }.get(brief.mode,"both")
    user = f"原型分析：{json.dumps(analysis,ensure_ascii=False)}\n方向：{brief.direction}\n补充指令：{brief.instruction}\n数量：{brief.count}\n路线要求：{mode_rule}"
    text = await ark_chat([{"role":"system","content":system},{"role":"user","content":user}])
    try:
        data=json.loads(text); return [{"id":f"plan-{i+1:03}",**p,"match":90-i,"color":"orange" if i==0 else "blue","image_url":None,"status":"ready","source":"ark"} for i,p in enumerate(data[:brief.count])]
    except Exception: return fallback_concepts()[:brief.count]

async def generate_image(prompt, path: Path|None):
    model=os.getenv("ARK_IMAGE_MODEL","doubao-seedream-4-0-250828")
    if not configured() or not model: return None
    # Seedream Images API returns image URLs by default; response_format is not
    # accepted by some Endpoint versions, so keep the request minimal.
    payload={"model":model,"prompt":prompt,"size":os.getenv("ARK_IMAGE_SIZE","2K")}
    if path and path.exists():
        mime={".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"}.get(path.suffix.lower(),"image/png")
        payload["image"]=[f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"]
    async with httpx.AsyncClient(timeout=180) as client:
        r=await client.post(f"{ARK_BASE}/images/generations",headers=headers(),json=payload)
        if r.is_error:
            raise RuntimeError(f"Seedream HTTP {r.status_code}: {r.text[:800]}")
        body=r.json()
        return (body.get("data") or [{}])[0].get("url")

@app.get("/api/health")
async def health(): return {"status":"ok","service":"ForgeLab","ark_configured":configured(),"time":datetime.now(timezone.utc).isoformat()}
@app.get("/", include_in_schema=False)
async def frontend(): return FileResponse(ROOT / "index.html")
@app.get("/styles.css", include_in_schema=False)
async def styles(): return FileResponse(ROOT / "styles.css", media_type="text/css", headers={"Cache-Control":"no-store"})
@app.get("/app.js", include_in_schema=False)
async def script(): return FileResponse(ROOT / "app.js", media_type="text/javascript", headers={"Cache-Control":"no-store"})
@app.get("/api/config")
async def config(): return {"ark_configured":configured(),"vision_model":bool(os.getenv("ARK_VISION_MODEL")),"llm_model":bool(os.getenv("ARK_LLM_MODEL")),"image_model":bool(os.getenv("ARK_IMAGE_MODEL"))}
@app.post("/api/config")
async def update_config(data: ApiConfigInput):
    if not data.api_key.strip().startswith("ark-"):
        raise HTTPException(400, "API Key 格式不正确，应以 ark- 开头")
    save_env_config(data)
    return {"ok": True, "ark_configured": True, "message": "配置已安全保存到本机"}
@app.post("/api/analyze-description")
async def analyze_description(data: DescriptionInput):
    prompt=ANALYSIS_PROMPT+f"\n用户描述如下：\n{data.description}"
    text=await ark_chat([{"role":"user","content":prompt}])
    try: return {**json.loads(text),"confidence":85.0,"source":"ark-text"}
    except Exception: return {"appearance":"待补充","functions":data.description,"play":"待补充","principle":"待补充","mechanics":"待补充","electronics":"待补充","selling_points":"待补充","reusable_traits":"待补充","pain_points":"待补充","confidence":60.0,"source":"fallback"}
@app.get("/api/projects")
async def list_projects(): return {"items":projects}
@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    p=next((x for x in projects if x["id"]==project_id),None)
    if not p: raise HTTPException(404,"项目不存在")
    return {**p,"analysis":{"appearance":"圆润的机器人探索车体，主体为哑光白色，顶部配有橙色透明观察舱。","mechanics":"四轮独立驱动结构","confidence":98.4},"plans":fallback_concepts()}
@app.post("/api/assets/upload")
async def upload_asset(file: UploadFile=File(...)):
    suffix=Path(file.filename or "asset.bin").suffix.lower()
    if suffix not in {".png",".jpg",".jpeg",".webp",".mp4",".mov"}: raise HTTPException(400,"仅支持图片或短视频")
    asset_id=uuid4().hex
    target=UPLOADS/f"{asset_id}{suffix}"; target.write_bytes(await file.read())
    asset_paths[asset_id]=target
    try:
            analysis=await analyze_asset(target)
    except httpx.HTTPStatusError as exc:
            analysis={"source":"fallback","message":f"视觉 API 返回 HTTP {exc.response.status_code}，已保存素材并使用本地降级分析。请在方舟控制台填入可用的视觉 Endpoint ID。","appearance":"圆润的白色陪伴机器人，黑色屏幕显示绿色笑脸，带有圆角头部、双侧耳翼、四肢关节与短尾巴。","mechanics":"可见为双臂双腿关节结构，内部电子组件无法从图片确认。","confidence":78.0}
    except Exception as exc:
            analysis={"source":"fallback","message":f"视觉 API 调用失败：{type(exc).__name__}","appearance":"圆润的白色陪伴机器人，黑色屏幕显示绿色笑脸，带有圆角头部、双侧耳翼、四肢关节与短尾巴。","mechanics":"内部结构图片不可见。","confidence":78.0}
    if suffix in {".mp4",".mov"}:
        frame=UPLOADS/f"{target.stem}-frame-0.jpg"
        if frame.exists(): asset_paths[asset_id]=frame
    return {"id":asset_id,"filename":file.filename,"size":target.stat().st_size,"url":f"/api/assets/{target.name}","analysis":analysis}
@app.get("/api/assets/{name}")
async def asset(name:str):
    target=UPLOADS/Path(name).name
    if not target.exists(): raise HTTPException(404,"素材不存在")
    return FileResponse(target)
@app.post("/api/projects/{project_id}/generate")
async def generate(project_id:str,brief:Brief):
    if not any(x["id"]==project_id for x in projects): raise HTTPException(404,"项目不存在")
    job_id=uuid4().hex; jobs[job_id]={"id":job_id,"project_id":project_id,"status":"queued","progress":0,"plans":[],"provider":"ark" if configured() else "fallback"}
    asyncio.create_task(run_job(job_id,brief)); return jobs[job_id]
async def run_job(job_id,brief):
    try:
        jobs[job_id].update(status="running",progress=20); await asyncio.sleep(.1)
        analysis=brief.analysis or (await get_project("proj-001"))["analysis"]
        plans=await generate_with_llm(brief,analysis); jobs[job_id].update(progress=75,plans=plans)
        reference_path=asset_paths.get(brief.asset_id)
        if configured() and os.getenv("ARK_IMAGE_MODEL"):
            for p in plans:
                try:
                    if brief.mode == "feature" or str(p.get("type","")).startswith("B"):
                        strict_prompt=(p.get("image_prompt") or p["appearance"])+" Create a commercially plausible new toy that transfers the core interaction and user value from the reference, with clear product photography and manufacturable construction."
                        image_reference=None
                    else:
                        strict_prompt=(p.get("image_prompt") or p["appearance"])+" Preserve the exact silhouette, head-to-body ratio, pose, screen position, limb count, joint locations, paw footprint and mechanical layout of the reference toy. Change only the cosmetic outer shell surfaces, decorative details, materials and colors. Product photography, same camera angle."
                        image_reference=reference_path
                    p["image_url"]=await generate_image(strict_prompt,image_reference)
                except Exception as e: p["image_error"]=str(e)
        jobs[job_id].update(status="completed",progress=100)
    except Exception as e: jobs[job_id].update(status="failed",error=str(e))
@app.get("/api/jobs/{job_id}")
async def job(job_id:str):
    if job_id not in jobs: raise HTTPException(404,"任务不存在")
    return jobs[job_id]
@app.get("/api/projects/{project_id}/export.md")
async def export_markdown(project_id:str):
    project=await get_project(project_id); lines=[f"# {project['name']} · 产品方案报告","","## 视觉结构摘要",project["analysis"]["appearance"],"","## 方案集",""]
    for p in project["plans"]: lines += [f"### {p['name']}",f"- 类型：{p['type']}",f"- 结构匹配：{p['match']}%",f"- 外观描述：{p['appearance']}",f"- 改动点：{p['changes']}",""]
    return Response("\n".join(lines),media_type="text/markdown",headers={"Content-Disposition":"attachment; filename=forgelab-report.md"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
