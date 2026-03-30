"""UniRig AI 자동 리깅 — 로컬 GPU에서 실행."""
import os
import subprocess
from pathlib import Path

VENDOR_DIR = Path(__file__).parent.parent / "vendor" / "UniRig"


def _find_conda_env() -> str:
    """unirig conda 환경의 Python 경로를 찾는다."""
    result = subprocess.run(
        ["conda", "run", "-n", "unirig", "which", "python"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    # 폴백: 일반적인 conda 경로
    home = os.path.expanduser("~")
    candidates = [
        f"{home}/miniconda3/envs/unirig/bin/python",
        f"{home}/anaconda3/envs/unirig/bin/python",
        f"{home}/mambaforge/envs/unirig/bin/python",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    raise FileNotFoundError(
        "unirig conda 환경을 찾을 수 없습니다. setup_unirig.sh를 먼저 실행하세요."
    )


def _run_unirig_script(script_name: str, args: list[str], timeout: int = 300):
    """UniRig launch 스크립트를 conda 환경에서 실행한다."""
    script_path = VENDOR_DIR / "launch" / "inference" / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"UniRig 스크립트 없음: {script_path}")

    result = subprocess.run(
        ["conda", "run", "-n", "unirig", "bash", str(script_path)] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(VENDOR_DIR),
    )

    # 출력에서 중요 메시지 추출
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line and not line.startswith(("["):
            if any(kw in line.lower() for kw in ["error", "complete", "saving", "loading", "skeleton", "skin"]):
                print(f"  → {line[:120]}")

    if result.returncode != 0:
        stderr_tail = result.stderr[-500:] if result.stderr else ""
        stdout_tail = result.stdout[-500:] if result.stdout else ""
        raise RuntimeError(
            f"UniRig {script_name} 실패 (exit {result.returncode})\n"
            f"stderr: {stderr_tail}\nstdout: {stdout_tail}"
        )


def unirig_rig(input_glb: str | Path, output_dir: str | Path) -> Path:
    """UniRig로 3D 메쉬를 자동 리깅한다.

    3단계: 스켈레톤 생성 → 스킨닝 → 원본 메쉬와 머지

    Returns: 리깅된 GLB 파일 경로
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
            f"setup_unirig.sh를 먼저 실행하세요."
        )

    # Step 1: 스켈레톤 생성
    print("[Step 2a/3] UniRig 스켈레톤 생성 중...")
    _run_unirig_script("generate_skeleton.sh", [
        "--input", str(input_glb),
        "--output", str(skeleton_path),
    ])

    if not skeleton_path.exists():
        raise FileNotFoundError(f"스켈레톤 생성 실패: {skeleton_path}")
    print(f"  → 스켈레톤: {skeleton_path} ({skeleton_path.stat().st_size / 1024:.0f}KB)")

    # Step 2: 스킨닝
    print("[Step 2b/3] UniRig 스킨닝 중...")
    _run_unirig_script("generate_skin.sh", [
        "--input", str(skeleton_path),
        "--output", str(skin_path),
    ])

    if not skin_path.exists():
        raise FileNotFoundError(f"스킨닝 실패: {skin_path}")
    print(f"  → 스킨: {skin_path} ({skin_path.stat().st_size / 1024:.0f}KB)")

    # Step 3: 머지
    print("[Step 2c/3] UniRig 머지 중...")
    _run_unirig_script("merge.sh", [
        "--source", str(skin_path),
        "--target", str(input_glb),
        "--output", str(rigged_path),
    ])

    if not rigged_path.exists():
        # 머지 실패 시 skin.fbx를 결과로 사용
        print("  → GLB 머지 실패, FBX를 결과로 사용")
        rigged_path = skin_path

    print(f"  → 리깅 완료: {rigged_path} ({rigged_path.stat().st_size / 1024:.0f}KB)")
    return rigged_path
