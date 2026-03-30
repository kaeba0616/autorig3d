"""Step 2: 3D 메쉬 자동 리깅 — UniRig(AI) 우선, Blender(템플릿) 폴백."""
import os
import subprocess
from pathlib import Path

BLENDER_SCRIPT_PATH = Path(__file__).parent / "blender_rig.py"


def auto_rig(input_glb: str | Path, output_dir: str | Path, mode: str = "auto") -> Path:
    """GLB 메쉬를 자동 리깅한다.

    Args:
        mode: "auto" (UniRig 시도 → Blender 폴백), "unirig", "blender"
    """
    input_glb = Path(input_glb)
    output_dir = Path(output_dir)

    if mode == "auto":
        # UniRig 시도 → 실패하면 Blender 폴백
        try:
            return _unirig_rig(input_glb, output_dir)
        except Exception as e:
            print(f"  ⚠ UniRig 실패: {e}")
            print(f"  → Blender 템플릿 리깅으로 폴백")
            return _blender_rig(input_glb, output_dir)
    elif mode == "unirig":
        return _unirig_rig(input_glb, output_dir)
    else:
        return _blender_rig(input_glb, output_dir)


def _unirig_rig(input_glb: Path, output_dir: Path) -> Path:
    """UniRig AI 리깅."""
    from .unirig import unirig_rig
    return unirig_rig(input_glb, output_dir)


def _blender_rig(input_glb: Path, output_dir: Path) -> Path:
    """Blender 템플릿 리깅 (기존 방식)."""
    output_glb = output_dir / "rigged_model.glb"

    print("[Step 2/3] Blender 템플릿 리깅 중...")

    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    if "VIRTUAL_ENV" in os.environ:
        venv_bin = os.path.join(os.environ["VIRTUAL_ENV"], "bin")
        env["PATH"] = ":".join(
            p for p in env.get("PATH", "").split(":") if p != venv_bin
        )

    result = subprocess.run(
        [
            "blender", "--background", "--python", str(BLENDER_SCRIPT_PATH),
            "--", str(input_glb.resolve()), str(output_glb.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    for line in result.stdout.split("\n"):
        if line.startswith(("메쉬 발견", "리깅 완료", "내보내기 완료", "ERROR")):
            print(f"  → {line}")

    if result.returncode != 0:
        print(f"  [stderr] {result.stderr[-500:]}")
        error_lines = [l for l in result.stderr.split("\n") if "Error" in l or "error" in l.lower()]
        raise RuntimeError(f"Blender 리깅 실패: {'; '.join(error_lines[:3])}")

    if not output_glb.exists():
        fbx_path = output_dir / "rigged_model.fbx"
        if fbx_path.exists():
            print(f"  → GLB 실패, FBX로 대체: {fbx_path}")
            output_glb = fbx_path
        else:
            raise FileNotFoundError(f"리깅된 모델이 생성되지 않았습니다: {output_glb}")

    size_kb = output_glb.stat().st_size / 1024
    print(f"  → 리깅된 모델: {output_glb} ({size_kb:.0f}KB)")
    return output_glb


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.auto_rig <input.glb> [output_dir] [--mode unirig|blender|auto]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "/tmp/autorig3d_output"
    mode = "auto"
    if "--mode" in sys.argv:
        mode = sys.argv[sys.argv.index("--mode") + 1]

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    rigged = auto_rig(input_path, output_dir, mode=mode)
    print(f"\n완료: {rigged}")
