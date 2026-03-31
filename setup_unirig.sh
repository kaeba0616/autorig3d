#!/bin/bash
# UniRig 로컬 설치 스크립트 (RTX 5080 / CUDA 12.x 기준)
# 사용법: ./setup_unirig.sh
set -e

echo "=== UniRig 로컬 설치 (RTX 5080) ==="

# 0. CUDA 확인
echo "[0/5] CUDA 확인..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    CUDA_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
    echo "  Driver: $CUDA_VER"
else
    echo "❌ nvidia-smi 없음 — CUDA가 설치되어 있는지 확인하세요"
    exit 1
fi

# 1. UniRig 클론
if [ ! -d "vendor/UniRig" ]; then
    echo "[1/5] UniRig 클론 중..."
    mkdir -p vendor
    git clone https://github.com/VAST-AI-Research/UniRig vendor/UniRig
else
    echo "[1/5] UniRig 이미 존재"
fi

# 2. conda 확인 + 환경 생성
if ! command -v conda &> /dev/null; then
    echo "❌ conda가 설치되어 있지 않습니다."
    echo "   설치: https://docs.conda.io/en/latest/miniconda.html"
    echo "   또는: wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi

if ! conda env list | grep -q "unirig"; then
    echo "[2/5] conda 환경 생성 (Python 3.11)..."
    conda create -n unirig python=3.11 -y
else
    echo "[2/5] conda 환경 이미 존재"
fi

# 3. conda 활성화 + 의존성 설치
echo "[3/5] 의존성 설치 중..."
eval "$(conda shell.bash hook)"
conda activate unirig

cd vendor/UniRig

# PyTorch (CUDA 12.4 — 5080 호환)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# requirements.txt (bpy는 별도 처리)
sed -i '/^bpy/d' requirements.txt
pip install -r requirements.txt
pip install numpy==1.26.4

cd ../..

# 4. spconv + 관련 패키지
echo "[4/5] spconv + 부가 패키지 설치 중..."
eval "$(conda shell.bash hook)"
conda activate unirig

# cumm 먼저 (spconv 의존성)
pip install cumm-cu124 2>/dev/null || \
pip install cumm-cu121 2>/dev/null || \
pip install cumm-cu120 2>/dev/null || \
echo "⚠ cumm 프리빌드 없음 — 소스 빌드 시도"

# spconv
pip install spconv-cu124 2>/dev/null || \
pip install spconv-cu121 2>/dev/null || \
pip install spconv-cu120 2>/dev/null || \
echo "⚠ spconv 설치 실패 — 아래 수동 설치 참조"

# torch_scatter, torch_cluster
TORCH_VERSION=$(python -c "import torch; print(torch.__version__.split('+')[0])")
CUDA_SHORT=$(python -c "import torch; print(torch.version.cuda.replace('.','')[:3])")
pip install torch_scatter torch_cluster \
    -f "https://data.pyg.org/whl/torch-${TORCH_VERSION}+cu${CUDA_SHORT}.html" 2>/dev/null || \
    echo "⚠ torch_scatter/cluster 설치 실패"

# flash_attn (선택적, 성능 향상)
pip install flash_attn 2>/dev/null || echo "⚠ flash_attn 건너뜀 (선택적)"

# bpy (Blender Python — 로컬에서는 설치 가능)
pip install bpy 2>/dev/null || echo "⚠ bpy 설치 실패 — extract.py 패치 적용"

# 5. 설치 확인
echo "[5/5] 설치 확인..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')

errors = []
for pkg in ['lightning', 'transformers', 'trimesh', 'open3d', 'einops']:
    try:
        __import__(pkg)
    except ImportError:
        errors.append(pkg)

try:
    import spconv
    print('spconv: ✅')
except Exception as e:
    print(f'spconv: ❌ ({e})')
    errors.append('spconv')

if errors:
    print(f'\\n⚠ 누락된 패키지: {errors}')
else:
    print('\\n✅ 모든 의존성 설치 완료!')
"

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "사용법:"
echo "  conda activate unirig"
echo "  cd $(pwd)"
echo "  python -m pipeline.run 이미지.png --mode unirig"
