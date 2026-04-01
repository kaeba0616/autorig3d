"""전체 파이프라인: 이미지 → 3D 메쉬 → 자동 리깅 → VRM 출력."""
import shutil
from pathlib import Path

from .mesh_gen import image_to_3d
from .auto_rig import auto_rig
from .vrm_convert import convert_to_vrm

# 프로젝트 루트의 output/ 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_BASE = PROJECT_ROOT / "output"


def run_pipeline(image_path: str | Path, output_dir: str | Path = None, rig_mode: str = "auto") -> dict:
    """이미지 한 장에서 리깅된 3D 모델을 생성한다.

    Args:
        rig_mode: "auto" (UniRig → Blender 폴백), "unirig", "blender"

    Returns:
        {"output_dir": str, "mesh_path": str, "rigged_path": str}
    """
    image_path = Path(image_path)

    if output_dir is None:
        # 이미지 파일명(확장자 제외)으로 폴더 생성
        folder_name = image_path.stem
        output_dir = OUTPUT_BASE / folder_name

    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # 원본 이미지를 output 폴더에 복사
    shutil.copy2(image_path, output_dir / f"original{image_path.suffix}")

    # Step 1: 이미지 → 3D 메쉬
    mesh_path = image_to_3d(image_path, output_dir)

    # Step 2: 3D 메쉬 → 자동 리깅
    rigged_path = auto_rig(mesh_path, output_dir, mode=rig_mode)

    # Step 3: 리깅된 모델 → VRM 변환
    vrm_path = None
    try:
        vrm_path = convert_to_vrm(rigged_path, output_dir)
    except Exception as e:
        print(f"  ⚠ VRM 변환 실패: {e}")
        print(f"  → GLB/FBX 파일은 정상 생성됨. VRM은 수동 변환 필요.")

    print(f"\n{'='*50}")
    print(f"파이프라인 완료!")
    print(f"  원본 메쉬: {mesh_path}")
    print(f"  리깅 모델: {rigged_path}")
    if vrm_path:
        print(f"  VRM 모델: {vrm_path}")
        print(f"\nVSeeFace에서 {vrm_path} 를 열면 VTuber로 사용 가능합니다.")
    else:
        print(f"\nGLB/FBX 파일을 3D 뷰어에서 확인하세요.")

    return {
        "output_dir": str(output_dir),
        "mesh_path": str(mesh_path),
        "rigged_path": str(rigged_path),
        "vrm_path": str(vrm_path) if vrm_path else None,
    }


def rig_existing_model(model_path: str | Path, output_dir: str | Path = None, rig_mode: str = "auto") -> dict:
    """기존 GLB/FBX 모델에 리깅 + VRM 변환만 수행한다."""
    model_path = Path(model_path)

    if output_dir is None:
        output_dir = OUTPUT_BASE / model_path.stem
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 모델 파일을 output에 복사 (원본이 다른 곳에 있을 수 있음)
    dest_model = output_dir / model_path.name
    if model_path.resolve() != dest_model.resolve():
        shutil.copy2(model_path, dest_model)

    # Step 1: 리깅
    print(f"[Step 1/2] 자동 리깅 중 (mode={rig_mode})...")
    rigged_path = auto_rig(dest_model, output_dir, mode=rig_mode)

    # Step 2: VRM 변환
    vrm_path = None
    try:
        vrm_path = convert_to_vrm(rigged_path, output_dir)
    except Exception as e:
        print(f"  ⚠ VRM 변환 실패: {e}")

    print(f"\n{'='*50}")
    print(f"리깅 완료!")
    print(f"  원본 모델: {dest_model}")
    print(f"  리깅 모델: {rigged_path}")
    if vrm_path:
        print(f"  VRM 모델: {vrm_path}")

    return {
        "output_dir": str(output_dir),
        "mesh_path": str(dest_model),
        "rigged_path": str(rigged_path),
        "vrm_path": str(vrm_path) if vrm_path else None,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  이미지 → 3D → 리깅:")
        print("    python -m pipeline.run character.png [--mode unirig|blender|auto]")
        print("")
        print("  기존 GLB/FBX → 리깅:")
        print("    python -m pipeline.run model.glb --rig-only [--mode unirig|blender|auto]")
        sys.exit(1)

    input_path = sys.argv[1]
    rig_mode = "auto"
    if "--mode" in sys.argv:
        rig_mode = sys.argv[sys.argv.index("--mode") + 1]

    rig_only = "--rig-only" in sys.argv

    if rig_only:
        result = rig_existing_model(input_path, rig_mode=rig_mode)
    else:
        result = run_pipeline(input_path, rig_mode=rig_mode)
