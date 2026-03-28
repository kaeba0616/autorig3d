"""Step 3: 리깅된 모델 → VRM 변환."""
import subprocess
import os
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent / "blender_vrm.py"


def convert_to_vrm(input_file: str | Path, output_dir: str | Path) -> Path:
    """리깅된 GLB/FBX를 VRM으로 변환한다."""
    input_file = Path(input_file)
    output_dir = Path(output_dir)
    output_vrm = output_dir / "model.vrm"

    print("[Step 3/3] VRM 변환 중...")

    # venv 환경변수 제거
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    if "VIRTUAL_ENV" in os.environ:
        venv_bin = os.path.join(os.environ["VIRTUAL_ENV"], "bin")
        env["PATH"] = ":".join(
            p for p in env.get("PATH", "").split(":") if p != venv_bin
        )

    result = subprocess.run(
        [
            "blender", "--background", "--python", str(SCRIPT_PATH),
            "--", str(input_file.resolve()), str(output_vrm.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    # 출력에서 중요 메시지 추출
    for line in result.stdout.split("\n"):
        if line.startswith(("아마추어", "메쉬", "VRM", "ERROR")):
            print(f"  → {line}")

    if result.returncode != 0:
        print(f"  [stderr] {result.stderr[-300:]}")
        raise RuntimeError("VRM 변환 실패")

    if not output_vrm.exists():
        print(f"  [stdout] {result.stdout[-300:]}")
        raise FileNotFoundError(f"VRM 파일이 생성되지 않았습니다: {output_vrm}")

    size_kb = output_vrm.stat().st_size / 1024
    print(f"  → VRM 모델: {output_vrm} ({size_kb:.0f}KB)")
    return output_vrm
