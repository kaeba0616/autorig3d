"""Step 2: Blender로 3D 메쉬 자동 리깅."""
import subprocess
from pathlib import Path

# blender_rig.py의 경로
SCRIPT_PATH = Path(__file__).parent / "blender_rig.py"


def auto_rig(input_glb: str | Path, output_dir: str | Path) -> Path:
    """GLB 메쉬에 자동으로 휴머노이드 스켈레톤을 추가하고 웨이트 페인팅한다."""
    input_glb = Path(input_glb)
    output_dir = Path(output_dir)
    output_glb = output_dir / "rigged_model.glb"

    print("[Step 2/3] Blender로 자동 리깅 중...")

    # venv 환경변수를 제거해서 Blender가 시스템 Python을 사용하도록
    import os
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    # PATH에서 venv 경로 제거
    if "VIRTUAL_ENV" in os.environ:
        venv_bin = os.path.join(os.environ["VIRTUAL_ENV"], "bin")
        env["PATH"] = ":".join(
            p for p in env.get("PATH", "").split(":") if p != venv_bin
        )

    result = subprocess.run(
        [
            "blender", "--background", "--python", str(SCRIPT_PATH),
            "--", str(input_glb.resolve()), str(output_glb.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    # 출력에서 중요 메시지 추출
    for line in result.stdout.split("\n"):
        if line.startswith(("메쉬 발견", "리깅 완료", "내보내기 완료", "ERROR")):
            print(f"  → {line}")

    if result.returncode != 0:
        print(f"  [stderr] {result.stderr[-500:]}")
        print(f"  [stdout] {result.stdout[-500:]}")
        error_lines = [l for l in result.stderr.split("\n") if "Error" in l or "error" in l.lower()]
        raise RuntimeError(f"Blender 리깅 실패: {'; '.join(error_lines[:3])}")

    if not output_glb.exists():
        # FBX 폴백 확인
        fbx_path = output_dir / "rigged_model.fbx"
        if fbx_path.exists():
            print(f"  → GLB 내보내기 실패, FBX로 대체: {fbx_path}")
            output_glb = fbx_path
        else:
            print(f"  [stdout] {result.stdout[-500:]}")
            print(f"  [stderr] {result.stderr[-500:]}")
            raise FileNotFoundError(f"리깅된 모델이 생성되지 않았습니다: {output_glb}")

    size_kb = output_glb.stat().st_size / 1024
    print(f"  → 리깅된 모델: {output_glb} ({size_kb:.0f}KB)")
    return output_glb


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.auto_rig <input.glb> [output_dir]")
        sys.exit(1)

    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/autorig3d_output"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    rigged = auto_rig(sys.argv[1], output_dir)
    print(f"\n완료: {rigged}")
