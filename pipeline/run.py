"""전체 파이프라인: 이미지 → 3D 메쉬 → 자동 리깅 → GLB 출력."""
import shutil
from pathlib import Path

from .mesh_gen import image_to_3d
from .auto_rig import auto_rig


def run_pipeline(image_path: str | Path, output_dir: str | Path = None) -> dict:
    """이미지 한 장에서 리깅된 3D 모델을 생성한다.

    Returns:
        {"output_dir": str, "mesh_path": str, "rigged_path": str}
    """
    image_path = Path(image_path)
    if output_dir is None:
        output_dir = Path("/tmp/autorig3d_output")

    output_dir = Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Step 1: 이미지 → 3D 메쉬
    mesh_path = image_to_3d(image_path, output_dir)

    # Step 2: 3D 메쉬 → 자동 리깅
    rigged_path = auto_rig(mesh_path, output_dir)

    print(f"\n{'='*50}")
    print(f"파이프라인 완료!")
    print(f"  원본 메쉬: {mesh_path}")
    print(f"  리깅 모델: {rigged_path}")
    print(f"\n이 GLB 파일을 3D 뷰어에서 열어 확인하세요.")
    print(f"VRM 변환 후 VSeeFace에서 VTuber로 사용 가능합니다.")

    return {
        "output_dir": str(output_dir),
        "mesh_path": str(mesh_path),
        "rigged_path": str(rigged_path),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.run <image_path> [output_dir]")
        print("Example: python -m pipeline.run character.png ./output")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    result = run_pipeline(image_path, output_dir)
