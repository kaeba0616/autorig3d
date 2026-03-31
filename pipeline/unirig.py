"""UniRig AI 자동 리깅 — 로컬 GPU (RTX 5080/5090)에서 실행."""
import os
import subprocess
import shutil
from pathlib import Path

VENDOR_DIR = Path(__file__).parent.parent / "vendor" / "UniRig"


def _get_conda_run_cmd() -> list[str]:
    """conda run 커맨드를 반환한다."""
    # conda run으로 unirig 환경에서 실행
    return ["conda", "run", "--no-capture-output", "-n", "unirig"]


def _run_cmd(args: list[str], timeout: int = 600, cwd: str = None):
    """conda unirig 환경에서 명령어를 실행한다."""
    cmd = _get_conda_run_cmd() + args
    if cwd is None:
        cwd = str(VENDOR_DIR)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )

    # 중요 메시지 출력
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line and any(kw in line.lower() for kw in
                       ["error", "complete", "saving", "loading", "skeleton", "skin", "done", "추출"]):
            print(f"  → {line[:150]}")

    if result.returncode != 0:
        stderr = result.stderr[-800:] if result.stderr else ""
        stdout = result.stdout[-800:] if result.stdout else ""
        raise RuntimeError(
            f"UniRig 실패 (exit {result.returncode})\n"
            f"stderr: {stderr}\nstdout: {stdout}"
        )

    return result


def unirig_rig(input_glb: str | Path, output_dir: str | Path) -> Path:
    """UniRig로 3D 메쉬를 자동 리깅한다.

    3단계: 메쉬 추출 + 스켈레톤 생성 → 스킨닝 → 머지

    Returns: 리깅된 GLB/FBX 파일 경로
    """
    input_glb = Path(input_glb).resolve()
    output_dir = Path(output_dir).resolve()

    skeleton_path = output_dir / "skeleton.fbx"
    skin_path = output_dir / "skin.fbx"
    rigged_path = output_dir / "rigged_model.glb"

    # UniRig 설치 확인
    if not VENDOR_DIR.exists():
        raise FileNotFoundError(
            f"UniRig가 설치되지 않았습니다: {VENDOR_DIR}\n"
            f"./setup_unirig.sh를 먼저 실행하세요."
        )

    # Step 1: 스켈레톤 생성 (메쉬 추출 + 추론)
    print("[Step 2a/3] UniRig 스켈레톤 생성 중...")
    _run_cmd([
        "bash", "launch/inference/generate_skeleton.sh",
        "--input", str(input_glb),
        "--output", str(skeleton_path),
    ])

    if not skeleton_path.exists():
        raise FileNotFoundError(f"스켈레톤 생성 실패: {skeleton_path}")
    print(f"  → 스켈레톤: {skeleton_path.stat().st_size / 1024:.0f}KB")

    # Step 2: 스킨닝 (웨이트 페인팅)
    print("[Step 2b/3] UniRig 스킨닝 중...")
    _run_cmd([
        "bash", "launch/inference/generate_skin.sh",
        "--input", str(skeleton_path),
        "--output", str(skin_path),
    ])

    if not skin_path.exists():
        raise FileNotFoundError(f"스킨닝 실패: {skin_path}")
    print(f"  → 스킨: {skin_path.stat().st_size / 1024:.0f}KB")

    # Step 3: 머지 (원본 메쉬 + 리깅 결합)
    print("[Step 2c/3] UniRig 머지 중...")
    _run_cmd([
        "bash", "launch/inference/merge.sh",
        "--source", str(skin_path),
        "--target", str(input_glb),
        "--output", str(rigged_path),
    ])

    if not rigged_path.exists():
        # 머지 실패 시 skin.fbx를 결과로
        print("  → GLB 머지 실패, FBX 사용")
        rigged_path = skin_path

    size_kb = rigged_path.stat().st_size / 1024
    print(f"  → 리깅 완료: {rigged_path} ({size_kb:.0f}KB)")
    return rigged_path
