#!/bin/bash
# UniRig 로컬 설치 스크립트 (RTX 5080 / CUDA 12.x 기준)
set -e

echo "=== UniRig 로컬 설치 ==="

# 1. UniRig 클론
if [ ! -d "vendor/UniRig" ]; then
    echo "[1/4] UniRig 클론 중..."
    mkdir -p vendor
    git clone https://github.com/VAST-AI-Research/UniRig vendor/UniRig
else
    echo "[1/4] UniRig 이미 존재"
fi

# 2. conda 환경 생성
if ! conda env list | grep -q "unirig"; then
    echo "[2/4] conda 환경 생성 (Python 3.11)..."
    conda create -n unirig python=3.11 -y
else
    echo "[2/4] conda 환경 이미 존재"
fi

# 3. 의존성 설치
echo "[3/4] 의존성 설치 중..."
eval "$(conda shell.bash hook)"
conda activate unirig

cd vendor/UniRig
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
pip install numpy==1.26.4

# spconv (CUDA 12.x)
pip install spconv-cu120 2>/dev/null || pip install spconv-cu121 2>/dev/null || echo "spconv 설치 실패 — 수동 설치 필요"

# torch_scatter, torch_cluster
TORCH_VERSION=$(python -c "import torch; print(torch.__version__.split('+')[0])")
CUDA_VERSION=$(python -c "import torch; print(torch.version.cuda.replace('.','')[:3])")
pip install torch_scatter torch_cluster \
    -f "https://data.pyg.org/whl/torch-${TORCH_VERSION}+cu${CUDA_VERSION}.html" 2>/dev/null || \
    echo "torch_scatter/cluster 설치 실패 — 수동 설치 필요"

cd ../..

# 4. 테스트
echo "[4/4] GPU 테스트..."
conda activate unirig
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}GB')
"

echo ""
echo "=== 설치 완료 ==="
echo "사용법: conda activate unirig && python -m pipeline.run 이미지.png --rig-mode unirig"
