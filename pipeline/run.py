"""전체 파이프라인: 이미지 → 3D 메쉬 → 자동 리깅 → VRM 출력."""
import shutil
from pathlib import Path

from .mesh_gen import image_to_3d
from .auto_rig import auto_rig
from .vrm_convert import convert_to_vrm

# 프로젝트 루트의 output/ 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_BASE = PROJECT_ROOT / "output"


def run_pipeline(image_path: str | Path, output_dir: str | Path = None) -> dict:
    """이미지 한 장에서 리깅된 3D 모델을 생성한다.

    output_dir을 지정하지 않으면 ~/dev/autorig3d/output/{이미지이름}/ 에 저장.

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
    rigged_path = auto_rig(mesh_path, output_dir)

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


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.run <image_path> [output_dir]")
        print("Example: python -m pipeline.run character.png ./output")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    result = run_pipeline(image_path, output_dir)
