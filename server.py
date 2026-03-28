"""AutoRig3D 웹 서버."""
import base64
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from pipeline.mesh_gen import image_to_3d
from pipeline.auto_rig import auto_rig

load_dotenv()

app = FastAPI(title="AutoRig3D", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OUTPUT_BASE = Path(__file__).parent / "output"
WEB_DIR = Path(__file__).parent / "web"


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.post("/api/generate")
async def generate(file: UploadFile = File(...)):
    """이미지 → 3D 모델 → 자동 리깅."""
    content = await file.read()

    # 이미지 이름으로 output 폴더 생성
    stem = Path(file.filename or "model").stem
    output_dir = OUTPUT_BASE / stem
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # 원본 이미지 저장
    ext = Path(file.filename or "img.png").suffix or ".png"
    image_path = output_dir / f"original{ext}"
    image_path.write_bytes(content)

    # Step 1: 이미지 → 3D
    try:
        mesh_path = image_to_3d(str(image_path), str(output_dir))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"3D 생성 실패: {e}", "step": 1})

    # Step 2: 자동 리깅
    try:
        rigged_path = auto_rig(str(mesh_path), str(output_dir))
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": f"리깅 실패: {e}", "step": 2,
            "mesh_path": str(mesh_path),
        })

    return {
        "name": stem,
        "mesh_file": mesh_path.name,
        "rigged_file": rigged_path.name,
        "output_dir": str(output_dir),
        "download_url": f"/output/{stem}/{rigged_path.name}",
        "mesh_download_url": f"/output/{stem}/{mesh_path.name}",
    }


@app.get("/output/{name}/{filename}")
async def download_file(name: str, filename: str):
    """생성된 파일 다운로드."""
    file_path = OUTPUT_BASE / name / filename
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "파일을 찾을 수 없습니다."})
    return FileResponse(file_path, filename=filename)


@app.get("/api/history")
async def history():
    """이전 생성 결과 목록."""
    if not OUTPUT_BASE.exists():
        return {"items": []}

    items = []
    for d in sorted(OUTPUT_BASE.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        files = [f.name for f in d.iterdir() if f.is_file()]
        rigged = next((f for f in files if f.startswith("rigged_")), None)
        mesh = next((f for f in files if f == "model.glb"), None)
        items.append({
            "name": d.name,
            "rigged_file": rigged,
            "mesh_file": mesh,
            "files": files,
        })

    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
