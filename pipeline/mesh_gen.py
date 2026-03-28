"""Step 1: Meshy API로 이미지 → 3D 메쉬 생성."""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MESHY_BASE = "https://api.meshy.ai/openapi/v1"


def _headers():
    return {
        "Authorization": f"Bearer {os.getenv('MESHY_API_KEY')}",
        "Content-Type": "application/json",
    }


def create_3d_from_image(image_path: str | Path) -> str:
    """이미지를 Meshy API에 base64로 전송하여 3D 모델 생성 태스크를 시작한다.

    Returns: task_id
    """
    import base64
    image_path = Path(image_path)

    # 이미지를 base64 data URI로 변환
    suffix = image_path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        suffix.lstrip("."), "image/png"
    )
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data_uri = f"data:{mime};base64,{b64}"

    resp = requests.post(
        f"{MESHY_BASE}/image-to-3d",
        headers=_headers(),
        json={
            "image_url": data_uri,
            "enable_pbr": True,
            "should_remesh": True,
            "should_texture": True,
        },
    )

    resp.raise_for_status()
    result = resp.json()
    task_id = result.get("result")
    print(f"  → Meshy 태스크 생성: {task_id}")
    return task_id


def poll_task(task_id: str, timeout: int = 600, interval: int = 10) -> dict:
    """태스크 완료까지 폴링한다.

    Returns: task result dict with model_urls
    """
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{MESHY_BASE}/image-to-3d/{task_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", "")
        progress = data.get("progress", 0)
        print(f"  → 상태: {status} ({progress}%)")

        if status == "SUCCEEDED":
            return data
        elif status == "FAILED":
            raise RuntimeError(f"Meshy 태스크 실패: {data.get('task_error', {})}")

        time.sleep(interval)

    raise TimeoutError(f"Meshy 태스크 {task_id} 타임아웃 ({timeout}초)")


def download_model(task_data: dict, output_dir: str | Path) -> Path:
    """완료된 태스크에서 GLB 모델을 다운로드한다."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_urls = task_data.get("model_urls", {})
    glb_url = model_urls.get("glb", "")

    if not glb_url:
        raise ValueError("GLB 다운로드 URL이 없습니다.")

    resp = requests.get(glb_url)
    resp.raise_for_status()

    output_path = output_dir / "model.glb"
    output_path.write_bytes(resp.content)
    print(f"  → 모델 다운로드: {output_path} ({len(resp.content) / 1024:.0f}KB)")
    return output_path


def image_to_3d(image_path: str | Path, output_dir: str | Path) -> Path:
    """이미지 → 3D GLB 모델 전체 흐름."""
    print("[Step 1/3] Meshy API로 3D 모델 생성 중...")
    task_id = create_3d_from_image(image_path)

    print("[Step 1/3] 3D 모델 생성 대기 중 (1-5분 소요)...")
    task_data = poll_task(task_id)

    return download_model(task_data, output_dir)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.mesh_gen <image_path> [output_dir]")
        sys.exit(1)

    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/autorig3d_output"
    glb_path = image_to_3d(sys.argv[1], output_dir)
    print(f"\n완료: {glb_path}")
