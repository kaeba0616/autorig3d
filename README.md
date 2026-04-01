# AutoRig3D

이미지 한 장 → 3D 모델 + 자동 리깅 + VRM 생성

캐릭터 일러스트를 넣으면 AI가 3D 모델로 변환하고, 자동으로 스켈레톤을 리깅합니다.

## 파이프라인

```
🧊 3D 모델만:
이미지 → [Meshy AI] → GLB 3D 모델

🎮 전체 파이프라인 (Blender):
이미지 → [Meshy AI] → GLB → [Blender 19본 리깅] → FBX/GLB → [VRM 변환] → VSeeFace

🤖 전체 파이프라인 (UniRig AI, GPU 필요):
이미지 → [Meshy AI] → GLB → [UniRig AI 리깅] → GLB → [VRM 변환] → VSeeFace
```

| 단계 | 도구 | 소요 시간 |
|------|------|----------|
| 3D 모델 생성 | Meshy API | 1-5분 |
| 자동 리깅 (Blender) | Blender headless | 5-10초 |
| 자동 리깅 (UniRig AI) | UniRig + GPU | 1-2분 |
| VRM 변환 | Blender VRM addon | 5초 |

---

## 설치 — 기본 (GPU 없이)

### 1. Blender + VRM 애드온

```bash
sudo apt install blender

curl -sL -o /tmp/vrm_addon.zip \
  "https://github.com/saturday06/VRM-Addon-for-Blender/releases/download/v3.24.0/VRM_Addon_for_Blender-3_24_0.zip"
mkdir -p ~/.config/blender/4.0/scripts/addons/
unzip -qo /tmp/vrm_addon.zip -d ~/.config/blender/4.0/scripts/addons/
```

### 2. Python 환경

```bash
git clone https://github.com/kaeba0616/autorig3d.git
cd autorig3d
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv fastapi uvicorn python-multipart
```

### 3. API 키

[Meshy](https://meshy.ai) 가입 후:

```bash
echo "MESHY_API_KEY=여기에_키" > .env
```

---

## 설치 — UniRig AI 리깅 (RTX 5080/5090 등 GPU 필요)

UniRig는 SIGGRAPH 2025 논문 기반 AI 리깅으로, 메쉬를 분석해서 최적의 본 배치 + 웨이트 페인팅을 자동 수행합니다.

### 요구 사항

- NVIDIA GPU (8GB+ VRAM) — RTX 3080, 4070, 5080 이상
- CUDA 12.x
- conda (Miniconda 또는 Anaconda)

### conda 설치 (없는 경우)

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# 설치 후 터미널 재시작
```

### UniRig 설치

```bash
cd autorig3d
./setup_unirig.sh
```

이 스크립트가 하는 일:
1. UniRig 레포 클론 (`vendor/UniRig`)
2. conda `unirig` 환경 생성 (Python 3.11)
3. PyTorch + CUDA 12.4 설치
4. spconv, cumm, flash_attn 등 의존성 설치
5. GPU 감지 + 설치 확인

설치 완료 후 의존성 확인에서 **전부 ✅**이면 성공입니다.

---

## 사용법

### 웹 UI (추천)

```bash
source .venv/bin/activate
python3 server.py
```

http://localhost:8000 접속:
- **🧊 3D 모델만** — 이미지 → GLB (리깅 없음)
- **🎮 전체 파이프라인** — 이미지 → 3D → 리깅 → VRM

### CLI — 전체 파이프라인

```bash
source .venv/bin/activate

# 기본 (UniRig 있으면 자동 사용, 없으면 Blender)
python3 -m pipeline.run 캐릭터이미지.png

# UniRig AI 리깅 (GPU 필요)
python3 -m pipeline.run 캐릭터이미지.png --mode unirig

# Blender 리깅만 (GPU 불필요)
python3 -m pipeline.run 캐릭터이미지.png --mode blender
```

### CLI — 3D 모델만 생성

```bash
source .venv/bin/activate
python3 -c "
from pipeline.mesh_gen import image_to_3d
image_to_3d('캐릭터이미지.png', './output/모델명')
"
```

### CLI — VRM 변환만

```bash
source .venv/bin/activate
python3 -c "
from pipeline.vrm_convert import convert_to_vrm
convert_to_vrm('output/모델명/rigged_model.glb', 'output/모델명')
"
```

---

## 출력 구조

```
output/
└── 캐릭터이름/
    ├── original.jpg        ← 원본 이미지
    ├── model.glb           ← 3D 메쉬 (리깅 전)
    ├── rigged_model.glb    ← 리깅된 모델 (또는 .fbx)
    └── model.vrm           ← VRM (VTuber용)
```

UniRig 사용 시 추가 파일:
```
    ├── skeleton.fbx        ← UniRig 스켈레톤
    └── skin.fbx            ← UniRig 스킨닝 결과
```

---

## 리깅 모드 비교

| 모드 | 도구 | 품질 | GPU | 속도 |
|------|------|------|-----|------|
| **auto** (기본) | UniRig → Blender 폴백 | 최선 자동 | 있으면 사용 | - |
| **unirig** | UniRig (SIGGRAPH 2025) | 최고 | 필수 (8GB+) | 1-2분 |
| **blender** | Blender 템플릿 19본 | 기본 | 불필요 | 5-10초 |

### UniRig vs Blender

| | UniRig AI | Blender 템플릿 |
|---|---|---|
| 본 배치 | 메쉬 형태를 분석해서 최적 배치 | 높이 비율로 고정 배치 |
| 웨이트 | AI가 학습된 패턴으로 페인팅 | Blender 기본 자동 웨이트 |
| 비표준 체형 | 잘 처리 (치비, 동물 등) | 어긋남 |
| 설치 | conda + CUDA + 의존성 다수 | sudo apt install blender |

---

## VTuber로 사용하기

1. `output/모델명/model.vrm` 다운로드
2. [VSeeFace](https://www.vseeface.icu/) 설치 (Windows, 무료)
3. VSeeFace → VRM 로드 → 웹캠 켜면 페이스 트래킹 시작

---

## 기술 스택

- Python 3.12+
- [Meshy API](https://meshy.ai) — 이미지 → 3D 모델
- [Blender](https://www.blender.org/) 4.0+ — 리깅 + VRM 변환
- [UniRig](https://github.com/VAST-AI-Research/UniRig) — AI 자동 리깅 (SIGGRAPH 2025)
- [VRM Addon](https://github.com/saturday06/VRM-Addon-for-Blender) — VRM 변환
- [FastAPI](https://fastapi.tiangolo.com/) — 웹 서버

---

## Docker로 실행 (5080 PC 배포용, 추천)

Docker를 사용하면 CUDA, spconv, UniRig 등 복잡한 의존성을 한 번에 해결합니다.

### 사전 요구

1. **Docker**: https://docs.docker.com/engine/install/
2. **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

```bash
# NVIDIA Container Toolkit 설치 (Ubuntu)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 빌드 + 실행

```bash
git clone https://github.com/kaeba0616/autorig3d.git
cd autorig3d

# API 키 설정
echo "MESHY_API_KEY=여기에_키" > .env

# 빌드 (최초 1회, 10-20분)
docker compose build

# 실행
docker compose up
```

http://localhost:8000 접속 → 이미지 드래그 → 완료.

### Docker CLI 사용

```bash
# 전체 파이프라인 (UniRig AI)
docker compose run autorig3d python -m pipeline.run /app/output/image.png --mode unirig

# 3D 모델만
docker compose run autorig3d python -c "
from pipeline.mesh_gen import image_to_3d
image_to_3d('/app/output/image.png', '/app/output/result')
"
```

`output/` 폴더는 호스트와 공유되므로, 결과 파일을 바로 확인할 수 있습니다.

---

## 문제 해결

| 문제 | 해결 |
|------|------|
| Meshy API 오류 | `.env`에 키 확인, 무료 크레딧 확인 |
| Blender GLB 내보내기 실패 | 자동 FBX 폴백 (정상) |
| VRM 변환 실패 | VRM 애드온 설치 확인. GLB/FBX는 정상 |
| UniRig 설치 실패 | `./setup_unirig.sh` 재실행, conda 필요 |
| UniRig spconv 오류 | CUDA 버전 확인: `nvidia-smi` |
| GPU 없음 | `--mode blender` 사용 |
| conda 없음 | Miniconda 설치 (위 가이드 참조) |
| Docker GPU 안 됨 | NVIDIA Container Toolkit 설치 확인 |
| Docker 빌드 느림 | 최초 1회만, 이후 캐시됨 |
